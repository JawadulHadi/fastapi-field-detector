"""Generate synthetic contracts with known ground truth.

Synthetic samples check the mechanics (layouts, labels, distractors). They do NOT replace real
contracts: add your own PDFs and labels to eval/samples to measure real-world accuracy.
"""
import json
from pathlib import Path

import pymupdf

OUT = Path(__file__).parent / 'samples'
W, H = 595, 842
HEIGHT = {'signature': 30, 'initials': 22, 'date': 16, 'name': 16}
BODY = ('This agreement is entered into on the date shown below by the parties named in it. '
        'Please sign here only after reading every clause carefully.')


def sample(name, items, body_lines=6):
    doc = pymupdf.open()
    page = doc.new_page(width=W, height=H)
    page.insert_text((60, 70), 'Service Agreement', fontsize=18)
    for i in range(body_lines):
        page.insert_text((60, 110 + i * 16), BODY[:85], fontsize=10)  # distractor text
    truth = []
    for it in items:
        x, y, label, kind, role = it['x'], it['y'], it['label'], it['kind'], it['role']
        if kind == 'checkbox':
            page.draw_rect(pymupdf.Rect(x, y - 9, x + 10, y + 1))
            page.insert_text((x + 18, y), label, fontsize=10)
            truth.append({'type': 'checkbox', 'role_key': role, 'page': 1,
                          'box': [x / W, (y - 9) / H, 10 / W, 10 / H]})
            continue
        page.insert_text((x, y), label, fontsize=11)
        label_w = pymupdf.get_text_length(label, fontsize=11)
        width = it.get('w', 150)
        if it.get('style', 'line') == 'line':
            lx = x + label_w + 8
            page.draw_line((lx, y + 2), (lx + width, y + 2))
        else:
            lx = x + label_w + 6
            page.insert_text((lx, y), '_' * int(width / 5.5), fontsize=11)
        h = HEIGHT[kind]
        truth.append({'type': kind, 'role_key': role, 'page': 1,
                      'box': [lx / W, (y + 2 - h) / H, width / W, h / H]})
    OUT.mkdir(exist_ok=True)
    (OUT / f'{name}.pdf').write_bytes(doc.tobytes())
    (OUT / f'{name}.json').write_text(json.dumps(truth, indent=1))


def sig(x, y, label, role, **kw):
    return {'x': x, 'y': y, 'label': label, 'kind': 'signature', 'role': role, **kw}


def field(kind, x, y, label, role, **kw):
    return {'x': x, 'y': y, 'label': label, 'kind': kind, 'role': role, **kw}


def main():
    sample('01_two_party', [
        sig(60, 600, 'Client Signature:', 'client'), field('date', 60, 640, 'Date:', 'client'),
        sig(330, 600, 'Contractor Signature:', 'contractor', w=130),
        field('date', 330, 640, 'Date:', 'contractor', w=130)])
    sample('02_underscores', [
        sig(60, 650, 'Employee Signature:', 'employee', style='underscore'),
        field('date', 60, 690, 'Date:', 'employee', style='underscore'),
        sig(60, 740, 'Employer Signature:', 'employer', style='underscore'),
        field('date', 60, 780, 'Date:', 'employer', style='underscore')])
    sample('03_printed_names', [
        sig(60, 600, 'Tenant Signature:', 'tenant'), field('name', 60, 635, 'Printed Name:', 'tenant'),
        field('date', 60, 670, 'Date:', 'tenant'),
        sig(60, 730, 'Landlord Signature:', 'landlord'),
        field('name', 60, 765, 'Printed Name:', 'landlord')])
    sample('04_initials_and_checkbox', [
        field('checkbox', 60, 560, 'I agree to the terms above', 'signer_1'),
        field('initials', 60, 600, 'Initials:', 'signer_1', w=60),
        sig(60, 660, 'Signature:', 'signer_1'), field('date', 60, 700, 'Date:', 'signer_1')])
    sample('05_witness', [
        sig(60, 600, 'Client Signature:', 'client'), field('date', 60, 636, 'Date:', 'client'),
        sig(60, 690, 'Witness Signature:', 'witness'), field('name', 60, 726, 'Witness Name:', 'witness')])
    sample('06_single', [sig(60, 700, 'Signed:', 'signer_1', w=200),
                         field('date', 60, 740, 'Date:', 'signer_1')])
    sample('07_buyer_seller', [
        sig(60, 620, 'Buyer Signature:', 'buyer', style='underscore'),
        sig(330, 620, 'Seller Signature:', 'seller', style='underscore', w=120),
        field('date', 60, 660, 'Date:', 'buyer', style='underscore'),
        field('date', 330, 660, 'Date:', 'seller', style='underscore', w=120)])
    sample('08_two_checkboxes', [
        field('checkbox', 60, 520, 'I have read the privacy notice', 'signer_1'),
        field('checkbox', 60, 545, 'I accept electronic delivery', 'signer_1'),
        sig(60, 640, 'Customer Signature:', 'customer'), field('date', 60, 680, 'Date:', 'customer')])
    sample('09_vendor_company', [
        sig(60, 560, 'Vendor Signature:', 'vendor'), field('name', 60, 596, 'Printed Name:', 'vendor'),
        sig(60, 660, 'Company Signature:', 'company'), field('name', 60, 696, 'Printed Name:', 'company'),
        field('date', 60, 732, 'Date:', 'company')])
    sample('10_no_fields', [], body_lines=10)
    print(f'wrote samples to {OUT}')


if __name__ == '__main__':
    main()

import re
from datetime import datetime

def pre_format_month(cc_raw):
    parts = cc_raw.strip().split('|')
    if len(parts) >= 3:
        cc = parts[0]
        if '/' in parts[1]:
            mm, yyyy = parts[1].split('/')
            mm = mm.zfill(2)
            yy = yyyy[-2:]
            cvv = parts[2]
            return f"{cc}|{mm}|{yy}|{cvv}"
        elif len(parts) >= 4:
            mm = parts[1].zfill(2)
            yy = parts[2][-2:]
            cvv = parts[3]
            return f"{cc}|{mm}|{yy}|{cvv}"
    return cc_raw

def normalize_unicode_bold(text):
    bold_upper = '𝗔𝗕𝗖𝗗𝗘𝗙𝗚𝗛𝗜𝗝𝗞𝗟𝗠𝗡𝗢𝗣𝗤𝗥𝗦𝗧𝗨𝗩𝗪𝗫𝗬𝗭'
    bold_lower = '𝗮𝗯𝗰𝗱𝗲𝗳𝗴𝗵𝗶𝗷𝗸𝗹𝗺𝗻𝗼𝗽𝗾𝗿𝘀𝘁𝘶𝘷𝘄𝘅𝘆𝘇'
    italic_upper = '𝘈𝘉𝘊𝘋𝘌𝘍𝘎𝘏𝘐𝘑𝘒𝘓𝘔𝘕𝘖𝘗𝘘𝘙𝘚𝘛𝘜𝘝𝘞𝘟𝘠𝘡'
    italic_lower = '𝘢𝘣𝘤𝘥𝘦𝘧𝘨𝘩𝘪𝘫𝘬𝘭𝘮𝘯𝘰𝘱𝘲𝘳𝘴𝘵𝘶𝘷𝘸𝘹𝘺𝘻'
    normal_upper = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    normal_lower = 'abcdefghijklmnopqrstuvwxyz'
    trans_table = str.maketrans(
        bold_upper + bold_lower + italic_upper + italic_lower,
        normal_upper + normal_lower + normal_upper + normal_lower
    )
    return text.translate(trans_table)

def extract_structured_card(message):
    card_match = re.search(r'Card[:\s]*([0-9]{13,19})', message, re.IGNORECASE)
    month_match = re.search(r'Exp\.?\s*month[:\s]*([0-9]{1,2})', message, re.IGNORECASE)
    year_match = re.search(r'Exp\.?\s*year[:\s]*([0-9]{2,4})', message, re.IGNORECASE)
    cvv_match = re.search(r'CVV[:\s]*([0-9]{3,4})', message, re.IGNORECASE)

    if card_match and month_match and year_match and cvv_match:
        card = card_match.group(1)
        month = month_match.group(1).zfill(2)
        year = year_match.group(1)[-2:]
        cvv = cvv_match.group(1)
        return f"{card}|{month}|{year}|{cvv}"
    return None

def reg(cc_raw):
    cc = pre_format_month(cc_raw)
    cc = normalize_unicode_bold(cc)
    cc = re.sub(r'[*_]+', '', cc)

    cvv = None
    exp_month = None
    exp_year = None
    cc_number = None

    cc_number_match = re.search(r'\b(?:NUMBER|NR)?\b[:\s]*([0-9]{12,19})', cc, re.IGNORECASE)
    if not cc_number_match:
        cc_number_match = re.search(r'([0-9]{12,19})', cc)
    if cc_number_match:
        cc_number = cc_number_match.group(1)

    cvv_match = re.search(r'\bCVV2?\b[:\s]*([0-9]{3,4})', cc, re.IGNORECASE)
    if not cvv_match:
        cvv_match = re.search(r'\bCVV\b[:\s]*([0-9]{3,4})', cc, re.IGNORECASE)
    if cvv_match:
        cvv = cvv_match.group(1)

    exp_match = re.search(r'\b(?:EXP(?:IRE)?|EXPIRY|EXP\s*DATE)?\b[:\s]*([0-9]{1,2})/([0-9]{2,4})', cc, re.IGNORECASE)
    if exp_match:
        exp_month = f"{int(exp_match.group(1)):02}"
        exp_year = exp_match.group(2)
        if len(exp_year) == 2:
            exp_year = f"20{exp_year}"

    if cc_number and exp_month and exp_year and cvv:
        return f"{cc_number}|{exp_month}|{exp_year}|{cvv}"

    matches = re.findall(r'\d+', cc)
    match = ''.join(matches)
    if len(match) < 18:
        return None

    if match.startswith(("34", "37")):
        n = match[:15]
        mm = match[15:17]
        yy = match[17:19]
        cvc_index = 19
        card_type = "AMEX"
    elif match.startswith("35"):
        n = match[:16]
        mm = match[16:18]
        yy = match[18:20]
        cvc_index = 20
        card_type = "JCB"
    else:
        n = match[:16]
        mm = match[16:18]
        yy = match[18:20]
        cvc_index = 20
        card_type = "OTHER"

    if yy == "20" and len(match) >= len(n) + 6:
        yy = match[len(n)+2:len(n)+6]
        cvc_index += 2

    cvc = match[cvc_index:cvc_index+4] if card_type == "AMEX" else match[cvc_index:cvc_index+3]

    if not n or not mm or not yy or not cvc:
        return None
    if not re.match(r'^\d{15,16}$', n):
        return None
    if not re.match(r'^\d{1,2}$', mm):
        return None
    if not re.match(r'^\d{2,4}$', yy):
        return None
    if (card_type == "AMEX" and not re.match(r'^\d{4}$', cvc)) or (card_type != "AMEX" and not re.match(r'^\d{3}$', cvc)):
        return None

    try:
        exp_month = int(mm)
        if exp_month < 1 or exp_month > 12:
            return None
    except:
        return None

    now = datetime.now()
    current_year = now.year % 100
    current_month = now.month

    exp_year = int(yy[-2:])
    if exp_year < current_year or (exp_year == current_year and exp_month < current_month):
        return None

    mm = f"{exp_month:02}"
    exp_month = mm
    exp_year = yy
    cc_number = n
    cvv = cvc

    return f"{cc_number}|{exp_month}|{exp_year}|{cvv}"

def extract_card_info(message):
    card_match = re.search(r'\b(\d{16})\b', message)
    card = card_match.group(1) if card_match else None

    cvv_match = re.search(r'cvv[:\s]*?(\d{3,4})', message, re.IGNORECASE)
    cvv = cvv_match.group(1) if cvv_match else None

    exp_match = re.search(
        r'(exp|expire|expiry|expiration)[:\s]*?(?:(\d{1,2})[\/\-](\d{2,4})|(\d{4}))',
        message, re.IGNORECASE
    )

    month = year = None
    if exp_match:
        if exp_match.group(2) and exp_match.group(3):
            month = exp_match.group(2).zfill(2)
            year = exp_match.group(3)[-2:]
        elif exp_match.group(4):
            month = exp_match.group(4)[:2]
            year = exp_match.group(4)[2:]

    if card and month and year and cvv:
        return f"{card}|{month}|{year}|{cvv}"
    return None

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import secrets
import os
import json
import string
import unicodedata
from datetime import datetime
from pathlib import Path
from colorama import Fore, Style, init

init(autoreset=True)

# ========== БЛОКИ СИМВОЛІВ З УСІМА ВАРІАНТАМИ ==========
def get_unicode_range(start, end, include_private=False):
    """Збирає символи із заданого діапазону Unicode, що є друкованими."""
    chars = []
    for code in range(start, end + 1):
        c = chr(code)
        cat = unicodedata.category(c)
        # виключаємо сурогати, керуючі символи, форматування (але залишаємо приватні якшо треба)
        if cat.startswith(('C', 'Z', 'M', 'S')) and not (include_private and cat == 'Co'):
            continue
        # виключаємо пробіли
        if c == ' ' or c == '\u00A0':
            continue
        chars.append(c)
    return ''.join(chars)

# Латиниця: базовий ASCII + Latin Extended-A, B, C, D, E, Additional, IPA Extensions
LATIN_BASIC = get_unicode_range(0x0041, 0x007A)  # A-Z a-z
LATIN_EXTENDED = (
    get_unicode_range(0x00C0, 0x024F)   # Latin-1 Supplement + Extended-A + Extended-B
    + get_unicode_range(0x1E00, 0x1EFF) # Latin Extended Additional
    + get_unicode_range(0x2C60, 0x2C7F) # Latin Extended-C
    + get_unicode_range(0xA720, 0xA7FF) # Latin Extended-D
    + get_unicode_range(0xAB30, 0xAB6F) # Latin Extended-E
)
LATIN_ALL = LATIN_BASIC + LATIN_EXTENDED

# Кирилиця: базова + supplement + extended
CYRILLIC_BASIC = get_unicode_range(0x0400, 0x04FF)   # Cyrillic
CYRILLIC_SUPPLEMENT = get_unicode_range(0x0500, 0x052F) # Cyrillic Supplement
CYRILLIC_EXTENDED = (
    get_unicode_range(0x2DE0, 0x2DFF)   # Cyrillic Extended-A
    + get_unicode_range(0xA640, 0xA69F) # Cyrillic Extended-B
)
CYRILLIC_ALL = CYRILLIC_BASIC + CYRILLIC_SUPPLEMENT + CYRILLIC_EXTENDED

# Грецька
GREEK_ALL = get_unicode_range(0x0370, 0x03FF)  # Greek and Coptic
GREEK_EXTENDED = get_unicode_range(0x1F00, 0x1FFF)  # Greek Extended
GREEK_FULL = GREEK_ALL + GREEK_EXTENDED

# Арабиця: базова + supplement + презентаційні форми A, B
ARABIC_BASIC = get_unicode_range(0x0600, 0x06FF)
ARABIC_SUPPLEMENT = get_unicode_range(0x0750, 0x077F)
ARABIC_PRES_FORMS_A = get_unicode_range(0xFB50, 0xFDFF)
ARABIC_PRES_FORMS_B = get_unicode_range(0xFE70, 0xFEFF)
ARABIC_ALL = ARABIC_BASIC + ARABIC_SUPPLEMENT + ARABIC_PRES_FORMS_A + ARABIC_PRES_FORMS_B

# Іврит: базовий + розширений
HEBREW_BASIC = get_unicode_range(0x0590, 0x05FF)
HEBREW_EXTENDED = get_unicode_range(0xFB1D, 0xFB4F)  # Alphabetic Presentation Forms (Hebrew)
HEBREW_ALL = HEBREW_BASIC + HEBREW_EXTENDED

# Деванагарі: базова + розширена
DEVANAGARI_BASIC = get_unicode_range(0x0900, 0x097F)
DEVANAGARI_EXTENDED = get_unicode_range(0xA8E0, 0xA8FF)  # Devanagari Extended
DEVANAGARI_FULL = DEVANAGARI_BASIC + DEVANAGARI_EXTENDED

# Тайська
THAI_ALL = get_unicode_range(0x0E00, 0x0E7F)

# Корейська: повний хангиль (склади) + хангиль Jamo (розширення)
HANGUL_SYLLABLES = get_unicode_range(0xAC00, 0xD7AF)  # Hangul Syllables
HANGUL_JAMO = get_unicode_range(0x1100, 0x11FF)       # Hangul Jamo
HANGUL_COMPAT_JAMO = get_unicode_range(0x3130, 0x318F) # Hangul Compatibility Jamo
HANGUL_ALL = HANGUL_SYLLABLES + HANGUL_JAMO + HANGUL_COMPAT_JAMO

# Японські азбуки: хірагана, катакана, halfwidth катакана
HIRAGANA_ALL = get_unicode_range(0x3040, 0x309F)
KATAKANA_ALL = get_unicode_range(0x30A0, 0x30FF)
KATAKANA_HALFWIDTH = get_unicode_range(0xFF65, 0xFF9F)  # Halfwidth Katakana
JAPANESE_KANA = HIRAGANA_ALL + KATAKANA_ALL + KATAKANA_HALFWIDTH

# Китайські ієрогліфи: обмежимо 3000 перших, щоб не було надто багато
def get_cjk_subset(count=3000):
    chars = []
    for code in range(0x4E00, 0x9FFF):
        if len(chars) >= count:
            break
        c = chr(code)
        if c.isprintable() and unicodedata.category(c).startswith('Lo'):
            chars.append(c)
    return ''.join(chars)
CJK_SMALL = get_cjk_subset(2000)

# Математичні символи
MATH_SYMBOLS = get_unicode_range(0x2200, 0x22FF)

# Стрілки
ARROWS = get_unicode_range(0x2190, 0x21FF)

# Геометричні фігури
GEOMETRIC = get_unicode_range(0x25A0, 0x25FF)

# Емодзі (вибірка)
EMOJI_BASIC = get_unicode_range(0x1F600, 0x1F64F)  # Emoticons
EMOJI_SUPP = get_unicode_range(0x1F300, 0x1F5FF)   # Misc Symbols and Pictographs

# Цифри (вже є в LATIN_BASIC, але додамо окремо для сумісності)
DIGITS_ONLY = string.digits
PUNCTUATION_ALL = string.punctuation  # стандартна ASCII пунктуація

# Групування за мовами (з варіантами)
LANGUAGE_SETS = {
    '1': ('Латиниця (усі варіанти)', LATIN_ALL),
    '2': ('Кирилиця (усі варіанти)', CYRILLIC_ALL),
    '3': ('Грецька (усі варіанти)', GREEK_FULL),
    '4': ('Арабиця (усі варіанти)', ARABIC_ALL),
    '5': ('Іврит (усі варіанти)', HEBREW_ALL),
    '6': ('Деванагарі (хінді, усі варіанти)', DEVANAGARI_FULL),
    '7': ('Тайська', THAI_ALL),
    '8': ('Корейська (усі варіанти)', HANGUL_ALL),
    '9': ('Японські азбуки (хірагана, катакана, halfwidth)', JAPANESE_KANA),
    '10': ('Китайські ієрогліфи (CJK, 2000 шт.)', CJK_SMALL),
    '11': ('Цифри', DIGITS_ONLY),
    '12': ('Пунктуація ASCII', PUNCTUATION_ALL),
    '13': ('Математичні символи', MATH_SYMBOLS),
    '14': ('Стрілки', ARROWS),
    '15': ('Геометричні фігури', GEOMETRIC),
    '16': ('Емодзі (базові)', EMOJI_BASIC + EMOJI_SUPP),
}

# ========== ДОПОМІЖНІ ФУНКЦІЇ ==========
def get_positive_integer(prompt, default=None):
    while True:
        if default is not None:
            prompt_with_default = f"{prompt} (за замовчуванням {default}): "
        else:
            prompt_with_default = prompt
        try:
            value = input(prompt_with_default).strip()
            if value == '' and default is not None:
                return default
            value = int(value)
            if value > 0:
                return value
            else:
                print(Fore.RED + "❌ Довжина має бути більше 0.")
        except ValueError:
            print(Fore.RED + "❌ Введіть ціле число.")

def yes_no_question(prompt, default='y'):
    valid = {'y': True, 'n': False, 'yes': True, 'no': False}
    if default == 'y':
        prompt = f"{prompt} [Y/n]: "
    else:
        prompt = f"{prompt} [y/N]: "
    while True:
        choice = input(prompt).strip().lower()
        if choice == '':
            return valid[default]
        if choice in valid:
            return valid[choice]
        print(Fore.RED + "❌ Відповідайте 'y' або 'n'.")

def select_character_sets():
    print(Fore.CYAN + "\n📚 Виберіть мови/набори (з усіма варіантами)")
    print(Fore.CYAN + "Введіть номери через кому (1,2,3), діапазон (1-5) або ALL для ВСЬОГО.\n")
    for key, (name, _) in LANGUAGE_SETS.items():
        print(f"  {key:>2}. {name}")

    while True:
        choice = input("\nВаш вибір: ").strip().lower()
        if choice == 'all':
            combined = ''
            for _, (_, charset) in LANGUAGE_SETS.items():
                combined += charset
            return combined

        selected_indices = []
        try:
            parts = [p.strip() for p in choice.split(',') if p.strip()]
            for part in parts:
                if '-' in part:
                    start, end = part.split('-')
                    for i in range(int(start), int(end)+1):
                        selected_indices.append(str(i))
                else:
                    selected_indices.append(part)
        except:
            print(Fore.RED + "❌ Неправильний формат. Спробуйте ще.")
            continue

        charset = ''
        valid = True
        for idx in selected_indices:
            if idx not in LANGUAGE_SETS:
                print(Fore.RED + f"❌ Невірний номер: {idx}")
                valid = False
                break
            charset += LANGUAGE_SETS[idx][1]
        if valid and charset:
            return charset

def estimate_entropy(password, charset_length):
    return len(password) * (charset_length.bit_length() if charset_length > 1 else 1)

def strength_label(bits):
    if bits < 56:
        return Fore.RED + "🔴 Слабкий"
    elif bits < 80:
        return Fore.YELLOW + "🟡 Середній"
    elif bits < 112:
        return Fore.GREEN + "🟢 Сильний"
    else:
        return Fore.BLUE + "🔵 Дуже сильний"

def save_passwords(passwords, purpose, file_format, file_path):
    file_path = Path(file_path)
    if not file_path.suffix:
        file_path = file_path.with_suffix(f'.{file_format}')
    file_path.parent.mkdir(parents=True, exist_ok=True)

    data = {
        'purpose': purpose,
        'generated': datetime.now().isoformat(),
        'passwords': passwords,
        'count': len(passwords),
    }

    if file_format == 'json':
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    elif file_format == 'csv':
        import csv
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['password', 'length'])
            for pwd in passwords:
                writer.writerow([pwd, len(pwd)])
    else:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(f"Purpose: {purpose}\n")
            f.write(f"Generated: {data['generated']}\n")
            f.write(f"Count: {len(passwords)}\n\n")
            for i, pwd in enumerate(passwords, 1):
                f.write(f"Password {i}: {pwd}\n")
    return file_path

def main():
    print(Fore.MAGENTA + Style.BRIGHT + "=" * 70)
    print(Fore.MAGENTA + Style.BRIGHT + "      ULTIMATE PASSWORD GENERATOR v3.0 (All Variants)")
    print(Fore.MAGENTA + Style.BRIGHT + "=" * 70)

    purpose = input(Fore.YELLOW + "\n📌 Призначення пароля: ").strip()
    if not purpose:
        purpose = "Без призначення"

    count = get_positive_integer(Fore.YELLOW + "🔢 Кількість паролів:", default=1)
    length = get_positive_integer(Fore.YELLOW + "🔢 Довжина пароля:", default=20)

    char_set = select_character_sets()
    unique_chars = len(set(char_set))
    print(Fore.GREEN + f"\n✅ Використовується {unique_chars:,} унікальних символів (усі варіанти мов).")

    passwords = []
    for _ in range(count):
        pwd = ''.join(secrets.choice(char_set) for _ in range(length))
        passwords.append(pwd)

    print(Fore.GREEN + f"\n🔐 Згенеровано {count} паролів:")
    for i, pwd in enumerate(passwords, 1):
        bits = estimate_entropy(pwd, unique_chars)
        print(f"  {i}. {Fore.WHITE}{pwd}  ({Fore.CYAN}ентропія: {bits} біт{strength_label(bits)}")

    if yes_no_question(Fore.YELLOW + "\n💾 Зберегти паролі у файл?", default='n'):
        print("Формат: txt, json, csv")
        while True:
            fmt = input("Формат: ").strip().lower()
            if fmt in ('txt', 'json', 'csv'):
                break
            print(Fore.RED + "❌ Введіть 'txt', 'json' або 'csv'.")
        path = input("Шлях до файлу: ").strip()
        if not path:
            path = f"{purpose.replace(' ', '_')}.{fmt}"
        try:
            saved = save_passwords(passwords, purpose, fmt, path)
            print(Fore.GREEN + f"✅ Збережено у {saved.resolve()}")
        except Exception as e:
            print(Fore.RED + f"❌ Помилка: {e}")

    print(Fore.CYAN + "\n👋 Готово!")

if __name__ == "__main__":
    main()
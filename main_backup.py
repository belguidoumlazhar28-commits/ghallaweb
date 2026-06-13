import flet as ft
import datetime
import os
import math
import re
import smtplib
import tempfile
import signal # إضافة مكتبة الإشارات
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from fpdf import FPDF
from arabic_reshaper import reshape
from bidi.algorithm import get_display
from pathlib import Path

# --- رقعة سحرية لتجاوز خطأ الإشارات في البيئات السحابية المقيدة (Streamlit/Render) ---
try:
    signal.signal(signal.SIGINT, signal.SIG_DFL)
except ValueError:
    # إذا رفض السيرفر تغيير الإشارات، نقوم بتعطيل الدالة تماماً لمنع الانهيار
    signal.signal = lambda *args, **kwargs: None
# -------------------------------------------------------------------------

# ----------------- الإعدادات الأمنية والبريد (Web Config) -----------------
WEB_CONFIG = {
    "ADMIN_PASSWORD": "ghalla projet",  # كلمة السر للدخول للتطبيق
    "SENDER_EMAIL": "belguidoumlazhar28@gmail.com", # بريد المصنع المرسل
    "RECEIVER_EMAIL": "belguidoumlazhar28@gmail.com",    # بريد المدير المستلم
    "APP_PASSWORD": "wjdi emln tovu sxbb",            # يجب وضع كلمة سر التطبيقات هنا
}

# ----------------- مساعدات معالجة النصوص والحسابات -----------------
def is_arabic(text):
    if not text: return False
    return any(u'\u0600' <= c <= u'\u06FF' for c in str(text))

def ar(text):
    if not text: return " "
    text = str(text)
    if not is_arabic(text): return text
    reshaped_text = reshape(text)
    return get_display(reshaped_text, base_dir='R')

def extract_float(text):
    text = str(text).strip()
    match = re.search(r'[-+]?\d*\.\d+|\d+', text)
    if match:
        return float(match.group())
    return 0.0

def format_unit(val):
    val_str = str(val).strip()
    if any(c.isalpha() for c in val_str) and not is_arabic(val_str):
        return val_str
    num = extract_float(val_str)
    if num == 0.0 and not any(char.isdigit() for char in val_str):
        return val_str
    if num.is_integer():
        return f"{int(num)} kg"
    return f"{num} kg"

# ----------------- فئة توليد الـ PDF الاحترافي للمؤسسة -----------------
class GhallaModernPDF(FPDF):
    def __init__(self):
        super().__init__()
        self.font_loaded = False
        script_dir = os.path.dirname(os.path.abspath(__file__))
        
        font_candidates = [
            os.path.join(script_dir, 'assets', 'Font.ttf'),
            os.path.join(script_dir, 'Font.ttf'),
            r'C:\Windows\Fonts\arial.ttf'
        ]
        
        for font_path in font_candidates:
            if os.path.exists(font_path):
                try:
                    self.add_font("ArabicFont", "", font_path)
                    self.font_loaded = True
                    break
                except Exception:
                    pass

    def header(self):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        logo_candidates = [
            os.path.join(script_dir, 'assets', 'logo.png'),
            os.path.join(script_dir, 'assets', '29640.jpg'),
            os.path.join(script_dir, 'assets', 'logo.jpg'),
            os.path.join(script_dir, 'logo.png')
        ]
        for logo_file in logo_candidates:
            if os.path.exists(logo_file):
                try:
                    self.image(logo_file, 85, 10, 40)
                    self.ln(42)
                    break
                except Exception:
                    pass
        else:
            self.ln(12)
        
        if self.font_loaded:
            self.set_font("ArabicFont", size=16)
        else:
            self.set_font("helvetica", size=16)
        
        self.set_text_color(26, 54, 93) 
        self.cell(0, 8, ar("التقرير اليومي للإنتاج"), new_x="LMARGIN", new_y="NEXT", align='C')
        
        self.set_font("helvetica", "B", size=13)
        self.set_text_color(34, 139, 34) 
        self.cell(0, 6, "SARL PLASTIQUE EL-GHALLA", new_x="LMARGIN", new_y="NEXT", align='C')
        
        self.set_draw_color(34, 139, 34)
        self.line(10, self.get_y() + 2, 200, self.get_y() + 2)
        self.ln(6)

    def footer(self):
        self.set_y(-15)
        if self.font_loaded:
            self.set_font("ArabicFont", size=9)
        else:
            self.set_font("helvetica", size=9)
            
        self.set_text_color(100, 100, 100)
        self.cell(95, 10, f"Page {self.page_no()}", align='L')
        self.cell(95, 10, "This system was built and developed by Ramzi Belguidoum", align='R')

    def draw_balanced_row(self, widths, row_data, base_height=8, is_header=False, fill_color=None, text_color=None):
        max_lines = 1
        for i, text in enumerate(row_data):
            processed_text = ar(text)
            string_width = self.get_string_width(processed_text)
            lines = math.ceil(string_width / (widths[i] - 3))
            if lines > max_lines:
                max_lines = lines
        
        total_row_height = max_lines * 6 if max_lines > 1 else base_height
        
        if self.get_y() + total_row_height > 275:
            self.add_page()
            
        x_start = self.get_x()
        y_start = self.get_y()
        
        for i, text in enumerate(row_data):
            self.set_xy(x_start, y_start)
            current_x = self.get_x()
            current_y = self.get_y()
            
            if is_header:
                self.set_fill_color(26, 54, 93) 
                self.set_text_color(255, 255, 255)
                self.cell(widths[i], total_row_height, "", border=1, fill=True)
            elif fill_color:
                self.set_fill_color(*fill_color)
                self.set_text_color(*(text_color if text_color else (0, 0, 0)))
                self.cell(widths[i], total_row_height, "", border=1, fill=True)
            else:
                self.set_fill_color(255, 255, 255)
                self.set_text_color(0, 0, 0)
                self.cell(widths[i], total_row_height, "", border=1, fill=False)
                
            text_height = max_lines * 5 if max_lines > 1 else base_height
            vertical_gap = (total_row_height - text_height) / 2
            self.set_xy(current_x, current_y + vertical_gap)
            
            self.multi_cell(widths[i], 5 if max_lines > 1 else base_height, ar(text), border=0, align='C')
            x_start += widths[i]
            
        self.set_xy(self.l_margin, y_start + total_row_height)

    def ensure_section_fits(self, estimated_rows_count, row_height=8):
        required_space = (estimated_rows_count + 1) * row_height + 15
        if self.get_y() + required_space > 275:
            self.add_page()

# ----------------- بداية معمارية الواجهة الرسومية Flet -----------------
ALL_MACHINES = [
    "خط الإنتاج رقم 01", "خط الإنتاج رقم 02", "خط الإنتاج رقم 03",
    "خط الإنتاج رقم 04", "خط الإنتاج رقم 05", "خط الإنتاج رقم 06",
    "خط الإنتاج رقم 07", "خط الإنتاج رقم 08", "خط الإنتاج رقم 09",
    "خط الإنتاج رقم 10", "خط إنتاج الغرانيلي", "خط إنتاج الموندرا",
    "خط إنتاج الخيط"
]

def main(page: ft.Page):
    page.title = "SARL PLASTIQUE EL-GHALLA - Production Dashboard"
    page.window_width = 550
    page.window_height = 880
    page.theme_mode = ft.ThemeMode.LIGHT
    page.scroll = ft.ScrollMode.AUTO
    page.rtl = True

    # تهيئة الحالة
    state = {
        "authenticated": False,
        "working_machines": [],
        "supervisor": "",
        "shift": "الصباحية",
        "production_data": {},
        "materials_data": {},
        "scrap_data": {},
        "downtimes": [],
        "hr_req": "0",
        "hr_act": "0",
        "hr_abs": "لا يوجد غيابات",
        "hr_acc": "لا توجد إصابات",
        "recommendations": "لا توجد توصيات إضافية.",
        "notes": "لا توجد ملاحظات تحذيرية مسجلة.",
        "current_machine_idx": 0,
        "generated_pdf_path": None
    }

    def send_email_report(file_path, file_name):
        """إرسال التقرير تلقائياً عبر البريد الإلكتروني"""
        if WEB_CONFIG["SENDER_EMAIL"] == "your-factory-email@gmail.com":
            return False # لم يتم إعداد البريد بعد
            
        try:
            msg = MIMEMultipart()
            msg['From'] = WEB_CONFIG["SENDER_EMAIL"]
            msg['To'] = WEB_CONFIG["RECEIVER_EMAIL"]
            msg['Subject'] = f"تقرير الإنتاج - {datetime.date.today()} - {state['shift']}"
            
            body = f"تحية طيبة،\n\nمرفق لكم التقرير اليومي لإنتاج المصنع لوردية {state['shift']}.\nتم توليد هذا التقرير آلياً عبر نظام الغلة الرقمي.\n\nتاريخ التقرير: {datetime.date.today()}"
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
            
            with open(file_path, "rb") as attachment:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(attachment.read())
                encoders.encode_base64(part)
                part.add_header("Content-Disposition", f"attachment; filename= {file_name}")
                msg.attach(part)
            
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(WEB_CONFIG["SENDER_EMAIL"], WEB_CONFIG["APP_PASSWORD"])
            server.send_message(msg)
            server.quit()
            return True
        except Exception as e:
            print(f"Email Error: {e}")
            return False

    def show_login_screen():
        pass_input = ft.TextField(
            label="أدخل كلمة سر النظام", 
            password=True, 
            can_reveal_password=True,
            text_align=ft.TextAlign.CENTER,
            on_submit=lambda e: check_auth()
        )
        
        def check_auth():
            if pass_input.value == WEB_CONFIG["ADMIN_PASSWORD"]:
                state["authenticated"] = True
                page.clean()
                page.add(header, main_content)
                show_step_machines()
            else:
                pass_input.error_text = "كلمة السر غير صحيحة!"
                page.update()

        page.clean()
        page.add(
            ft.Container(
                content=ft.Column([
                    ft.Icon(ft.icons.LOCK_PERSON, size=80, color="blue900"),
                    ft.Text("نظام إدارة الإنتاج - تسجيل الدخول", size=20, weight=ft.FontWeight.BOLD),
                    pass_input,
                    ft.FilledButton("دخول للنظام", on_click=lambda e: check_auth(), width=300, height=50)
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=20),
                padding=50,
                alignment=ft.alignment.center
            )
        )
        page.update()

    def get_logo_path():
        script_dir = os.path.dirname(os.path.abspath(__file__))
        logo_candidates = [
            os.path.join(script_dir, 'assets', 'logo.png'),
            os.path.join(script_dir, 'assets', '29640.jpg'),
            os.path.join(script_dir, 'assets', 'logo.jpg'),
            os.path.join(script_dir, 'logo.png')
        ]
        for path in logo_candidates:
            if os.path.exists(path):
                return path
        return None

    logo_path = get_logo_path()
    
    header = ft.Container(
        content=ft.Column([
            ft.Image(src=logo_path, width=100, height=100) if logo_path else ft.Icon(ft.icons.FACTORY, size=50, color="blue900"),
            ft.Text("مؤسسة الغلة للإنتاج", size=26, weight=ft.FontWeight.BOLD, color="blue900"),
            ft.Text("SARL PLASTIQUE EL-GHALLA", size=13, weight=ft.FontWeight.W_500, color="green700"),
            ft.Divider(height=2, color="blue200")
        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        padding=10
    )

    main_content = ft.Container(padding=15)

    def show_step_machines():
        state["current_machine_idx"] = 0
        machine_controls = []
        for m in ALL_MACHINES:
            is_checked = m in state["working_machines"]
            cb = ft.Checkbox(label=m, value=is_checked)
            def make_toggle(machine_name, checkbox_ref):
                return lambda e: state["working_machines"].append(machine_name) if checkbox_ref.value else state["working_machines"].remove(machine_name)
            cb.on_change = make_toggle(m, cb)
            machine_controls.append(cb)

        def confirm_machines(e):
            if not state["working_machines"]:
                error_dialog = ft.AlertDialog(title=ft.Text("تنبيه أمني فني", color="red"), content=ft.Text("يجب اختيار خط إنتاج واحد على الأقل للمتابعة!"))
                page.overlay.append(error_dialog)
                error_dialog.open = True
                page.update()
                return
            show_step_supervisor_shift()

        main_content.content = ft.Column([
            ft.Text("الخطوة 1: حدد خطوط الإنتاج الشغالة في هذه الوردية", size=16, weight=ft.FontWeight.BOLD, color="blue700"),
            ft.Column(machine_controls, spacing=5),
            ft.FilledButton(
                content=ft.Text("تأكيد خطوط الإنتاج والانتقال لبيانات الوردية ➔", color="white", weight=ft.FontWeight.BOLD),
                style=ft.ButtonStyle(bgcolor="blue800"),
                width=500,
                on_click=confirm_machines
            )
        ], spacing=15)
        page.update()

    def show_step_supervisor_shift():
        sup_input = ft.TextField(label="اسم المسؤول الحالي / رئيس الورشة", value=state["supervisor"], text_align=ft.TextAlign.RIGHT)
        shift_dropdown = ft.Dropdown(
            label="الوردية / المناوبة الحالية",
            value=state["shift"],
            options=[ft.dropdown.Option("الصباحية"), ft.dropdown.Option("المسائية"), ft.dropdown.Option("الليلية")]
        )

        def save_step(e):
            if not sup_input.value.strip():
                sup_input.error_text = "هذا الحقل إجباري لتوثيق النظام الإداري!"
                page.update()
                return
            state["supervisor"] = sup_input.value
            state["shift"] = shift_dropdown.value
            state["current_machine_idx"] = 0
            show_step_production()

        main_content.content = ft.Column([
            ft.Text("الخطوة 2: معلومات الوردية والمسؤول المباشر", size=16, weight=ft.FontWeight.BOLD, color="blue700"),
            sup_input,
            shift_dropdown,
            ft.Row([
                ft.TextButton(content=ft.Text("↩️ رجوع", color="bluegrey700", weight=ft.FontWeight.BOLD), on_click=lambda e: show_step_machines()),
                ft.FilledButton(content=ft.Text("التالي: إدخال مؤشرات الخطوط ➔", color="white"), style=ft.ButtonStyle(bgcolor="blue800"), on_click=save_step)
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
        ], spacing=15)
        page.update()

    def show_step_production():
        idx = state["current_machine_idx"]
        m_name = state["working_machines"][idx]
        
        if m_name not in state["production_data"]:
            state["production_data"][m_name] = []

        prod_input = ft.TextField(label="نوع المنتج والمواصفات (البلاستيك والمقاس)", text_align=ft.TextAlign.RIGHT)
        target_input = ft.TextField(label="الهدف المطلوب للآلة", value="0", keyboard_type=ft.KeyboardType.NUMBER, text_align=ft.TextAlign.RIGHT)
        actual_input = ft.TextField(label="المحقق فعلياً من الآلة", value="0", keyboard_type=ft.KeyboardType.NUMBER, text_align=ft.TextAlign.RIGHT)
        quality_input = ft.TextField(label="نسبة جودة المنتج المستهدفة (مثال: 98%)", value="100%", text_align=ft.TextAlign.RIGHT)

        added_items = []
        for p in state["production_data"][m_name]:
            added_items.append(ft.Text(f"• {p[0]} | الهدف: {p[1]} | المحقق: {p[2]} | كفاءة: {p[3]} | جودة: {p[4]}", size=12, color="green800"))

        def add_product_loop(e):
            if not prod_input.value.strip(): return
            t_num = extract_float(target_input.value)
            a_num = extract_float(actual_input.value)
            eff = min(int((a_num / t_num) * 100), 100) if t_num > 0 else 0
            
            state["production_data"][m_name].append([
                prod_input.value, target_input.value, actual_input.value, f"{eff} %", quality_input.value
            ])
            show_step_production()

        def go_next_section(e):
            if prod_input.value.strip():
                t_num = extract_float(target_input.value)
                a_num = extract_float(actual_input.value)
                eff = min(int((a_num / t_num) * 100), 100) if t_num > 0 else 0
                state["production_data"][m_name].append([
                    prod_input.value, target_input.value, actual_input.value, f"{eff} %", quality_input.value
                ])
            
            if not state["production_data"][m_name]:
                state["production_data"][m_name].append(["لم يتم إدخال منتج", "0", "0", "0 %", "0 %"])

            show_step_materials()

        def go_back_logic(e):
            if state["current_machine_idx"] == 0:
                show_step_supervisor_shift()
            else:
                state["current_machine_idx"] -= 1
                show_step_scrap()

        main_content.content = ft.Column([
            ft.Container(content=ft.Text(f"بيانات خط الإنتاج: {m_name} ({idx+1} من {len(state['working_machines'])})", weight=ft.FontWeight.BOLD, color="white"), bgcolor="blue700", padding=10, border_radius=5),
            ft.Column(added_items, spacing=2) if added_items else ft.Container(),
            prod_input,
            ft.Row([target_input, actual_input], spacing=10),
            quality_input,
            ft.FilledButton(content=ft.Text("➕ إضافة منتج آخر لخط الإنتاج الحالي", color="white"), style=ft.ButtonStyle(bgcolor="green700"), on_click=add_product_loop),
            ft.Divider(),
            ft.Row([
                ft.TextButton(content=ft.Text("↩️ رجوع", color="bluegrey700", weight=ft.FontWeight.BOLD), on_click=go_back_logic),
                ft.FilledButton(content=ft.Text("التالي: المواد الأولية المستهلكة ➔", color="white"), style=ft.ButtonStyle(bgcolor="blue800"), on_click=go_next_section)
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
        ], spacing=12)
        page.update()

    def show_step_materials():
        idx = state["current_machine_idx"]
        m_name = state["working_machines"][idx]

        if m_name not in state["materials_data"]:
            state["materials_data"][m_name] = []

        if "الغرانيلي" in m_name:
            state["materials_data"][m_name] = [["آلة تدوير مخلفات", "/"]]
            show_step_scrap()
            return

        mat_name = ft.TextField(label="اسم المادة الأولية", text_align=ft.TextAlign.RIGHT)
        mat_weight = ft.TextField(label="الوزن المستهلك (كغ)", text_align=ft.TextAlign.RIGHT)

        added_mats = []
        for mat in state["materials_data"][m_name]:
            added_mats.append(ft.Text(f"• {mat[0]} -> {mat[1]}", size=12, color="green800"))

        def add_material(e):
            if not mat_name.value.strip(): return
            w_formatted = format_unit(mat_weight.value)
            state["materials_data"][m_name].append([mat_name.value, w_formatted])
            show_step_materials()

        def proceed_to_scrap(e):
            if mat_name.value.strip():
                state["materials_data"][m_name].append([mat_name.value, format_unit(mat_weight.value)])
            if not state["materials_data"][m_name]:
                state["materials_data"][m_name] = [["غير محدد", "0 kg"]]
            show_step_scrap()

        main_content.content = ft.Column([
            ft.Container(content=ft.Text(f"📦 المواد المستهلكة لـ: {m_name}", weight=ft.FontWeight.BOLD, color="white"), bgcolor="green700", padding=10, border_radius=5),
            ft.Column(added_mats, spacing=2),
            mat_name,
            mat_weight,
            ft.FilledButton(content=ft.Text("➕ إضافة مادة أولية أخرى", color="white"), style=ft.ButtonStyle(bgcolor="green700"), on_click=add_material),
            ft.Divider(),
            ft.Row([
                ft.TextButton(content=ft.Text("↩️ رجوع", color="bluegrey700", weight=ft.FontWeight.BOLD), on_click=lambda e: show_step_production()),
                ft.FilledButton(content=ft.Text("التالي: تفاصيل المخلفات ➔", color="white"), style=ft.ButtonStyle(bgcolor="blue800"), on_click=proceed_to_scrap)
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
        ], spacing=12)
        page.update()

    def show_step_scrap():
        idx = state["current_machine_idx"]
        m_name = state["working_machines"][idx]

        if "الموندرا" in m_name or "الخيط" in m_name or "الغرانيلي" in m_name:
            state["scrap_data"][m_name] = ["لا توجد مخلفات", "(آلة مستثناة)"]
            move_next_machine_loop()
            return

        scrap_w = ft.TextField(label="وزن المخلفات الفعلي (Scrap)", value="0", text_align=ft.TextAlign.RIGHT)
        scrap_reason = ft.TextField(label="سبب وعلة ظهور هذه المخلفات بالتفصيل", multiline=True, text_align=ft.TextAlign.RIGHT)

        def save_scrap(e):
            w_formatted = format_unit(scrap_w.value)
            reason = scrap_reason.value.strip() if scrap_reason.value.strip() else "لا يوجد سبب محدد"
            state["scrap_data"][m_name] = [w_formatted, reason]
            move_next_machine_loop()

        def set_no_scrap(e):
            state["scrap_data"][m_name] = ["0", "لا يوجد"]
            move_next_machine_loop()

        main_content.content = ft.Column([
            ft.Container(content=ft.Text(f"🗑️ تفاصيل مخلفات (Scrap): {m_name}", weight=ft.FontWeight.BOLD, color="white"), bgcolor="red600", padding=10, border_radius=5),
            scrap_w,
            scrap_reason,
            ft.FilledButton(content=ft.Text("❌ لا توجد مخلفات لهذه الآلة", color="black"), style=ft.ButtonStyle(bgcolor="grey400"), on_click=set_no_scrap),
            ft.Row([
                ft.TextButton(content=ft.Text("↩️ رجوع", color="bluegrey700", weight=ft.FontWeight.BOLD), on_click=lambda e: show_step_materials()),
                ft.FilledButton(content=ft.Text("حفظ والانتقال للخطوة التالية ➔", color="white"), style=ft.ButtonStyle(bgcolor="blue800"), on_click=save_scrap)
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
        ], spacing=12)
        page.update()

    def move_next_machine_loop():
        if state["current_machine_idx"] + 1 < len(state["working_machines"]):
            state["current_machine_idx"] += 1
            show_step_production()
        else:
            show_step_downtimes()

    def show_step_downtimes():
        dt_machine_dd = ft.Dropdown(label="اختر الخط الذي حدث به العطل", options=[ft.dropdown.Option(m) for m in state["working_machines"]])
        dt_start = ft.TextField(label="وقت بداية التوقف (مثال: 08:30)", text_align=ft.TextAlign.RIGHT)
        dt_end = ft.TextField(label="وقت العودة والتشغيل (مثال: 09:15)", text_align=ft.TextAlign.RIGHT)
        dt_reason = ft.TextField(label="سبب العطل الفني بالتفصيل", text_align=ft.TextAlign.RIGHT)

        added_downtimes = []
        for dt in state["downtimes"]:
            added_downtimes.append(ft.Text(f"• {dt[0]} | من {dt[1]} إلى {dt[2]} | العطل: {dt[3]}", size=12, color="orange900"))

        def add_downtime(e):
            if not dt_machine_dd.value: return
            state["downtimes"].append([dt_machine_dd.value, dt_start.value, dt_end.value, dt_reason.value])
            show_step_downtimes()

        def go_back_to_loop(e):
            state["current_machine_idx"] = len(state["working_machines"]) - 1
            show_step_scrap()

        main_content.content = ft.Column([
            ft.Container(content=ft.Text("⚙️ القسم 2: سجل الأعطال والتوقفات الفنية للآلات (Downtime)", weight=ft.FontWeight.BOLD, color="white"), bgcolor="orange800", padding=10, border_radius=5),
            ft.Column(added_downtimes, spacing=2),
            dt_machine_dd,
            ft.Row([dt_start, dt_end], spacing=10),
            dt_reason,
            ft.FilledButton(content=ft.Text("➕ تسجيل هذا العطل في القائمة", color="white"), style=ft.ButtonStyle(bgcolor="orange700"), on_click=add_downtime),
            ft.Divider(),
            ft.Row([
                ft.TextButton(content=ft.Text("↩️ رجوع", color="bluegrey700", weight=ft.FontWeight.BOLD), on_click=go_back_to_loop),
                ft.FilledButton(content=ft.Text("التالي: الموارد البشرية ➔", color="white"), style=ft.ButtonStyle(bgcolor="blue800"), on_click=lambda e: show_step_hr())
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
        ], spacing=12)
        page.update()

    def show_step_hr():
        hr_req_in = ft.TextField(label="العدد المطلوب للعمال في الوردية", value=state["hr_req"], text_align=ft.TextAlign.RIGHT)
        hr_act_in = ft.TextField(label="الحضور الفعلي للعمال", value=state["hr_act"], text_align=ft.TextAlign.RIGHT)
        hr_abs_in = ft.TextField(label="تفاصيل الغيابات الحالية إن وجدت", value=state["hr_abs"], text_align=ft.TextAlign.RIGHT)
        hr_acc_in = ft.TextField(label="سجل إصابات العمل وحوادث السلامة المهنية", value=state["hr_acc"], text_align=ft.TextAlign.RIGHT)

        def save_hr(e):
            state["hr_req"] = hr_req_in.value
            state["hr_act"] = hr_act_in.value
            state["hr_abs"] = hr_abs_in.value
            state["hr_acc"] = hr_acc_in.value
            show_step_recommendations_notes()

        main_content.content = ft.Column([
            ft.Container(content=ft.Text("👥 القسم 3: الموارد البشرية والسلامة المهنية", weight=ft.FontWeight.BOLD, color="white"), bgcolor="teal700", padding=10, border_radius=5),
            ft.Row([hr_req_in, hr_act_in], spacing=10),
            hr_abs_in,
            hr_acc_in,
            ft.Row([
                ft.TextButton(content=ft.Text("↩️ رجوع", color="bluegrey700", weight=ft.FontWeight.BOLD), on_click=lambda e: show_step_downtimes()),
                ft.FilledButton(content=ft.Text("التالي: التوصيات والملاحظات ➔", color="white"), style=ft.ButtonStyle(bgcolor="blue800"), on_click=save_hr)
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
        ], spacing=12)
        page.update()

    def generate_pdf_locally():
        try:
            pdf = GhallaModernPDF()
            pdf.add_page()
            
            if pdf.font_loaded: pdf.set_font("ArabicFont", size=10)
            pdf.set_fill_color(240, 245, 240)
            today = datetime.date.today()
            today_str = today.strftime("%Y-%m-%d")
            
            pdf.cell(63.3, 9, today_str, border=1, align='C', fill=True, new_x="RIGHT", new_y="TOP")
            pdf.cell(63.3, 9, ar(f"رئيس الورشة: {state['supervisor']}"), border=1, align='C', fill=True, new_x="RIGHT", new_y="TOP")
            pdf.cell(63.3, 9, ar(f"الوردية: {state['shift']}"), border=1, align='C', fill=True, new_x="LMARGIN", new_y="NEXT")
            pdf.ln(6)
            
            working_m_list = [m for m in ALL_MACHINES if m in state["working_machines"]]
            
            # القسم 1
            total_prod_rows = sum(len(state["production_data"].get(m, [1])) for m in working_m_list)
            pdf.ensure_section_fits(total_prod_rows)
            if pdf.font_loaded: pdf.set_font("ArabicFont", size=12)
            pdf.set_fill_color(70, 130, 180); pdf.set_text_color(255, 255, 255)
            pdf.cell(0, 9, ar(" 1. وضعية خطوط الإنتاج الشغالة ومؤشرات الأداء"), new_x="LMARGIN", new_y="NEXT", align='R', fill=True)
            w_prod = [45, 50, 25, 25, 25, 20]
            headers_prod = ["خط الإنتاج", "المنتج والمواصفات", "الهدف المطلوب", "المحقق فعلياً", "نسبة الإنجاز", "الجودة"]
            pdf.draw_balanced_row(w_prod, headers_prod, base_height=8, is_header=True)
            if pdf.font_loaded: pdf.set_font("ArabicFont", size=9)
            for m in working_m_list:
                products = state["production_data"].get(m, [])
                if not products: products = [["بدون منتج", "0", "0", "0%", "0%"]]
                for idx, prod_data in enumerate(products):
                    machine_label = f"{m} (منتج {idx+1})" if len(products) > 1 else m
                    row_data = [machine_label, str(prod_data[0]), str(prod_data[1]), str(prod_data[2]), str(prod_data[3]), str(prod_data[4])]
                    pdf.draw_balanced_row(w_prod, row_data, base_height=8)
            pdf.ln(6)
            
            # القسم 2
            total_mat_rows = sum(len(state["materials_data"].get(m, [1])) for m in working_m_list)
            pdf.ensure_section_fits(total_mat_rows)
            if pdf.font_loaded: pdf.set_font("ArabicFont", size=12)
            pdf.set_fill_color(70, 130, 180); pdf.set_text_color(255, 255, 255)
            pdf.cell(0, 9, ar(" 2. جدول المواد المستهلكة (تفصيلي حسب كل آلة)"), new_x="LMARGIN", new_y="NEXT", align='R', fill=True)
            w_mat = [65, 65, 60]
            headers_mat = ["الآلة / خط الإنتاج", "اسم المادة الأولية", "الوزن المستهلك"]
            pdf.draw_balanced_row(w_mat, headers_mat, base_height=8, is_header=True)
            if pdf.font_loaded: pdf.set_font("ArabicFont", size=9)
            for m in working_m_list:
                m_materials = state["materials_data"].get(m, [["غير محدد", "0 kg"]])
                for item in m_materials:
                    pdf.draw_balanced_row(w_mat, [m, item[0], item[1]], base_height=8)
            pdf.ln(6)
            
            # القسم 3
            pdf.ensure_section_fits(len(working_m_list))
            if pdf.font_loaded: pdf.set_font("ArabicFont", size=12)
            pdf.set_fill_color(70, 130, 180); pdf.set_text_color(255, 255, 255)
            pdf.cell(0, 9, ar(" 3. بيان تفاصيل المخلفات (Scrap)"), new_x="LMARGIN", new_y="NEXT", align='R', fill=True)
            w_scrap = [55, 45, 90]
            headers_scrap = ["الآلة / خط الإنتاج", "وزن المخلفات", "سبب وعلة ظهور المخلفات بالتفصيل"]
            pdf.draw_balanced_row(w_scrap, headers_scrap, base_height=8, is_header=True)
            if pdf.font_loaded: pdf.set_font("ArabicFont", size=9)
            for m in working_m_list:
                scr = state["scrap_data"].get(m, ["0", "لا يوجد"])
                pdf.draw_balanced_row(w_scrap, [m, scr[0], scr[1]], base_height=8)
            pdf.ln(6)
            
            # القسم 4
            pdf.ensure_section_fits(max(len(state["downtimes"]), 1))
            if pdf.font_loaded: pdf.set_font("ArabicFont", size=12)
            pdf.set_fill_color(70, 130, 180); pdf.set_text_color(255, 255, 255)
            pdf.cell(0, 9, ar(" 4. سجل الأعطال والتوقفات الفنية للآلات (Downtime)"), new_x="LMARGIN", new_y="NEXT", align='R', fill=True)
            w_down = [50, 30, 30, 80]
            headers_down = ["الماكينة / الخط", "وقت التوقف", "وقت العودة", "سبب العطل الفني"]
            pdf.draw_balanced_row(w_down, headers_down, base_height=8, is_header=True)
            if pdf.font_loaded: pdf.set_font("ArabicFont", size=9)
            if not state["downtimes"]:
                pdf.draw_balanced_row(w_down, ["لا توجد أعطال", "00:00", "00:00", "كل الخطوط اشتغلت بكفاءة"], base_height=8)
            else:
                for dt in state["downtimes"]:
                    pdf.draw_balanced_row(w_down, dt, base_height=8)
            pdf.ln(6)
            
            # القسم 5
            pdf.ensure_section_fits(1)
            if pdf.font_loaded: pdf.set_font("ArabicFont", size=12)
            pdf.set_fill_color(70, 130, 180); pdf.set_text_color(255, 255, 255)
            pdf.cell(0, 9, ar(" 5. الموارد البشرية والسلامة المهنية"), new_x="LMARGIN", new_y="NEXT", align='R', fill=True)
            w_hr = [25, 25, 60, 80]
            headers_hr = ["العدد المطلوب", "الحضور الفعلي", "الغيابات", "إصابات العمل وحوادث السلامة المهنية"]
            pdf.draw_balanced_row(w_hr, headers_hr, base_height=8, is_header=True)
            if pdf.font_loaded: pdf.set_font("ArabicFont", size=9)
            pdf.draw_balanced_row(w_hr, [state["hr_req"], state["hr_act"], state["hr_abs"], state["hr_acc"]], base_height=8)
            pdf.ln(6)
            
            # القسم 6 و 7
            rec_lines = math.ceil(len(state["recommendations"]) / 50)
            notes_lines = math.ceil(len(state["notes"]) / 50)
            pdf.ensure_section_fits(rec_lines + notes_lines + 4)
            if pdf.font_loaded: pdf.set_font("ArabicFont", size=11)
            pdf.set_fill_color(220, 245, 220); pdf.set_text_color(34, 139, 34) 
            pdf.cell(0, 8, ar(" 6. التوصيات الفنية لرئيس الورشة للوردية التالية"), new_x="LMARGIN", new_y="NEXT", align='R', fill=True)
            pdf.set_text_color(0, 0, 0)
            pdf.multi_cell(0, 7, ar(state["recommendations"]), border='LRB', align='R')
            pdf.ln(4)
            pdf.set_fill_color(255, 220, 220); pdf.set_text_color(200, 0, 0) 
            pdf.cell(0, 8, ar(" 7. الملاحظات العامة والتحذيرات"), new_x="LMARGIN", new_y="NEXT", align='R', fill=True)
            pdf.set_text_color(0, 0, 0)
            pdf.multi_cell(0, 7, ar(state["notes"]), border='LRB', align='R')
            pdf.ln(12)
            
            pdf.ensure_section_fits(2)
            if pdf.font_loaded: pdf.set_font("ArabicFont", size=11)
            pdf.cell(63.3, 6, ar("توقيع رئيس الورشة"), border=0, align='C', new_x="RIGHT", new_y="TOP")
            pdf.cell(63.3, 6, ar("مراقب الجودة"), border=0, align='C', new_x="RIGHT", new_y="TOP")
            pdf.cell(63.3, 6, ar("اعتماد مدير المصنع"), border=0, align='C', new_x="LMARGIN", new_y="NEXT")
            pdf.cell(63.3, 10, "............................", border=0, align='C', new_x="RIGHT", new_y="TOP")
            pdf.cell(63.3, 10, "............................", border=0, align='C', new_x="RIGHT", new_y="TOP")
            pdf.cell(63.3, 10, "............................", border=0, align='C', new_x="LMARGIN", new_y="NEXT")

            # مسارات الحفظ (متوافقة مع الويب والمنصات السحابية)
            time_str = datetime.datetime.now().strftime("%H-%M-%S")
            file_name = f"Report_{state['shift']}_{time_str}.pdf"
            
            # استخدام مجلد مؤقت آمن للويب
            temp_dir = tempfile.gettempdir()
            full_path = os.path.join(temp_dir, file_name)
            
            # حفظ الملف
            pdf.output(full_path)
            state["generated_pdf_path"] = full_path
            
            # محاولة الإرسال عبر البريد
            email_sent = send_email_report(full_path, file_name)
            
            def download_file(e):
                # في الويب، نقوم بفتح الملف ليتمكن المتصفح من تحميله
                # ملاحظة: في النسخة الويب الحقيقية سنستخدم page.launch_url أو file_picker
                page.launch_url(f"file://{full_path}")

            def reset_app(e):
                state["working_machines"], state["production_data"], state["materials_data"], state["scrap_data"], state["downtimes"] = [], {}, {}, {}, []
                show_step_machines()

            email_status_text = "تم إرسال نسخة للمدير عبر البريد ✅" if email_sent else "لم يتم إعداد البريد التلقائي (أرشفة محلية فقط)"

            main_content.content = ft.Container(
                content=ft.Column([
                    ft.Icon(ft.icons.CHECK_CIRCLE_ROUNDED, color="green", size=80),
                    ft.Text("تم توليد التقرير بنجاح", size=24, weight=ft.FontWeight.BOLD, color="green900"),
                    ft.Text(email_status_text, size=14, color="bluegrey"),
                    ft.Divider(height=20, color="transparent"),
                    ft.Row([
                        ft.FilledButton(
                            content=ft.Text("تحميل التقرير PDF ⬇️", size=16),
                            style=ft.ButtonStyle(bgcolor="blue800"),
                            on_click=download_file,
                            width=200, height=50
                        ),
                        ft.OutlinedButton(
                            content=ft.Text("بدء تقرير جديد ↻", size=16),
                            on_click=reset_app,
                            width=200, height=50
                        )
                    ], alignment=ft.MainAxisAlignment.CENTER, spacing=10)
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=15),
                padding=40, alignment=ft.alignment.center
            )
            page.update()

        except Exception as ex:
            def close_error_dialog(e):
                error_dialog.open = False
                page.update()
            error_dialog = ft.AlertDialog(title=ft.Text(ar("خطأ في نظام حفظ الملفات"), color="red", weight=ft.FontWeight.BOLD), content=ft.Text(f"حدثت مشكلة أثناء محاولة حفظ المستند:\n{str(ex)}"), actions=[ft.TextButton(ar("إغلاق"), on_click=close_error_dialog)])
            page.overlay.append(error_dialog); error_dialog.open = True; page.update()

    def show_step_recommendations_notes():
        rec_in = ft.TextField(label="التوصيات الفنية لرئيس الورشة للوردية التالية", multiline=True, value=state["recommendations"], text_align=ft.TextAlign.RIGHT)
        notes_in = ft.TextField(label="الملاحظات العامة والتحذيرات الفنية للمصنع", multiline=True, value=state["notes"], text_align=ft.TextAlign.RIGHT)

        def run_final_generation(e):
            state["recommendations"], state["notes"] = rec_in.value, notes_in.value
            main_content.content = ft.Column([ft.ProgressRing(), ft.Text("جاري معالجة البيانات وتوليد التقرير الموحد...", size=16, color="blue800")], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=20)
            page.update()
            generate_pdf_locally()

        main_content.content = ft.Column([
            ft.Container(content=ft.Text("📝 القسم 4 و 5: التوصيات الميدانية والتحذيرات الفنية", weight=ft.FontWeight.BOLD, color="white"), bgcolor="bluegrey700", padding=10, border_radius=5),
            rec_in, notes_in,
            ft.Row([ft.TextButton(content=ft.Text("↩️ رجوع", color="bluegrey700", weight=ft.FontWeight.BOLD), on_click=lambda e: show_step_hr()), ft.FilledButton(content=ft.Text("إغلاق التقرير وتوليد وثيقة PDF نهائية 💾", color="white"), style=ft.ButtonStyle(bgcolor="red600"), height=45, on_click=run_final_generation)], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
        ], spacing=12)
        page.update()

    # البدء بشاشة تسجيل الدخول للحماية
    show_login_screen()

if __name__ == "__main__":
    # تشغيل التطبيق بنمط يتوافق مع قيود السحابة
    # نستخدم الحفظ التلقائي للمنفذ لتجنب التعارض
    ft.app(target=main)

import json
import ssl  # <- Thêm thư viện SSL cho
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.utils import get_color_from_hex
from kivy.core.window import Window
from kivy.network.urlrequest import UrlRequest
from kivy.graphics import Color, Rectangle, RoundedRectangle
import paho.mqtt.client as mqtt
# from kivy.animation import Animation
# Animation(rgba=new_color, duration=0.2).start(color_instr)

# --- CẤU HÌNH CỦA BẠN ---
# Thông tin MQTT đã được điền từ ảnh của bạn

# 1. Cấu hình MQTT
MQTT_BROKER_HOST = "4e01ee67ec4e475ca4c3b68e2703f19e.s1.eu.hivemq.cloud"
MQTT_BROKER_PORT = 8883  # QUAN TRỌNG: Đây là port 8883 (TLS/SSL)
MQTT_TOPIC = "Information"
MQTT_USERNAME = "Nhom3iot"  # <-- BẠN PHẢI ĐIỀN THÔNG TIN NÀY
MQTT_PASSWORD = "Nhom3iot"  # <-- BẠN PHẢI ĐIỀN THÔNG TIN NÀY

# 2. Cấu hình API
# Tôi đã điền API bạn cung cấp và GIẢ ĐỊNH tham số là "?bienso="
# Nếu API của bạn dùng tham số khác (vd: ?plate=), BẠN PHẢI SỬA DÒNG NÀY
API_HISTORY_URL_BASE = "https://z43k8t-8080.csb.app/parking-history/search?plate="

# --- KẾT THÚC CẤU HÌNH ---


# Set background color
Window.clearcolor = (0.95, 0.95, 0.95, 1)


# --- WIDGET 'CARD' TÙY CHỈNH (ĐÃ SỬA LỖI) ---
# --- WIDGET 'CARD' TÙY CHỈNH (ĐÃ SỬA LỖI LẦN 2) ---
class InfoCard(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = dp(15)
        self.spacing = dp(10)
        self.size_hint_y = None  # Để thẻ tự co giãn theo nội dung

        with self.canvas.before:
            Color(1, 1, 1, 1)  # Màu nền của thẻ (trắng)
            self.rect = RoundedRectangle(
                pos=self.pos,
                size=self.size,
                radius=[dp(10)]  # Bo góc
            )

        self.bind(pos=self.update_canvas, size=self.update_canvas)

        # [SỬA LỖI] Thay vì gán "height" một lần lúc nó bằng 0,
        # chúng ta "bind" nó để nó luôn tự cập nhật
        # khi "minimum_height" thay đổi (khi widget con được thêm vào).
        self.bind(minimum_height=self.setter('height'))

    def update_canvas(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size
# --- KẾT THÚC WIDGET 'CARD' ---

class ParkingApp(App):

    def build(self):
        """Build the main UI."""
        self.tab_panel = TabbedPanel(do_default_tab=False)
        self.tab_panel.background_color = (1, 1, 1, 1)

        # Tab 1: Dashboard
        self.tab_dashboard = TabbedPanelItem(text='Tổng quan')
        self.tab_dashboard.content = self.create_dashboard_tab()
        self.tab_panel.add_widget(self.tab_dashboard)

        # Tab 2: History
        self.tab_history = TabbedPanelItem(text='Lịch sử')
        self.tab_history.content = self.create_history_tab()
        self.tab_panel.add_widget(self.tab_history)

        return self.tab_panel

    def on_start(self):
        """Start the MQTT client connection."""
        try:
            # Kiểm tra xem người dùng đã điền thông tin chưa
            if "YOUR_" in MQTT_USERNAME or "YOUR_" in MQTT_PASSWORD:
                self.set_dashboard_status("LỖI: Vui lòng điền Username và Password\ncho MQTT trong file main.py", "red")
                return

            self.mqtt_client = mqtt.Client()
            self.mqtt_client.on_connect = self.on_mqtt_connect
            self.mqtt_client.on_message = self.on_mqtt_message

            self.mqtt_client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)

            # --- CẤU HÌNH TLS/SSL VÌ DÙNG PORT 8883 ---
            # Điều này là bắt buộc cho HiveMQ Cloud
            # self.mqtt_client.tls_set(tls_version=ssl.PROTOCOL_TLS)
            self.mqtt_client.tls_set(
                ca_certs="ca.crt",
                certfile=None,
                keyfile=None,
                tls_version=ssl.PROTOCOL_TLSv1_2
            )
            # ----------------------------------------

            self.mqtt_client.connect_async(MQTT_BROKER_HOST, MQTT_BROKER_PORT, 60)
            self.mqtt_client.loop_start()  # Start network loop in a separate thread
            self.set_dashboard_status("Đang kết nối MQTT...", "blue")
        except Exception as e:
            self.set_dashboard_status(f"Lỗi kết nối MQTT:\n{e}", "red")
            print(f"MQTT Connection Error: {e}")

    def on_stop(self):
        """Stop the MQTT client loop when the app closes."""
        if hasattr(self, 'mqtt_client'):
            self.mqtt_client.loop_stop()
            self.mqtt_client.disconnect()

    # --- MQTT Callbacks (run in a separate thread) ---

    def on_mqtt_connect(self, client, userdata, flags, rc):
        """Called when the client connects to the broker."""
        if rc == 0:
            print(f"Connected to MQTT broker and subscribing to '{MQTT_TOPIC}'")
            client.subscribe(MQTT_TOPIC)
            # Update UI from main thread
            Clock.schedule_once(lambda dt: self.set_dashboard_status("Đã kết nối. Chờ dữ liệu...", "green"))
        else:
            print(f"Failed to connect to MQTT, return code {rc}")
            Clock.schedule_once(
                lambda dt: self.set_dashboard_status(f"Lỗi kết nối MQTT: {rc}\n(Kiểm tra lại Username/Password)",
                                                     "red"))

    def on_mqtt_message(self, client, userdata, msg):
        """Called when a message is received from the broker."""
        try:
            payload = msg.payload.decode('utf-8')
            print(f"MQTT Message received on topic '{msg.topic}': {payload}")
            data = json.loads(payload)
            # Schedule UI update on the main thread
            Clock.schedule_once(lambda dt: self.update_dashboard(data))
        except Exception as e:
            print(f"Error processing MQTT message: {e}")
            Clock.schedule_once(lambda dt: self.set_dashboard_status(f"Lỗi xử lý message:\n{e}", "red"))

    # --- UI Update Functions (run on the main thread) ---

    def set_dashboard_status(self, text, status_type=""):
        """Update the main label to show status."""
        color = (0, 0, 0, 1)  # default black
        if status_type == "green":
            color = (0, 0.5, 0, 1)  # Dark green
        elif status_type == "red":
            color = (0.8, 0, 0, 1)  # Dark red
        elif status_type == "blue":
            color = (0.1, 0.1, 0.8, 1)  # Blue

        self.label_ten_bai.text = text
        self.label_ten_bai.color = color

    def update_dashboard(self, data):
        """Update dashboard labels with data from MQTT."""
        try:
            self.label_ten_bai.text = data.get('tenBai', 'N/A')
            self.label_ten_bai.color = (0, 0, 0, 1)
            self.label_dia_chi.text = data.get('diaChi', 'N/A')
            self.label_tong_slot.text = str(data.get('tongSlot', 'N/A'))
            self.label_nhiet_do.text = f"{data.get('nhietDo', 'N/A')} °C"
            self.label_do_am.text = f"{data.get('doAm', 'N/A')} %"

            status = data.get("status", {})
            available_count = sum(1 for v in status.values() if v == "available")
            self.label_slot_trong.text = str(available_count)

            # --- Cập nhật màu từng slot (MÀU MỚI) ---
            status = data.get("status", {})
            for key, (box, rect, color_instr) in self.slot_widgets.items():
                state = status.get(key, "unknown")
                if state == "occupied":
                    color_instr.rgba = get_color_from_hex('#ef4444')  # Đỏ
                elif state == "available":
                    color_instr.rgba = get_color_from_hex('#22c55e')  # Xanh lá
                else:
                    color_instr.rgba = get_color_from_hex('#9ca3af')  # Xám

                # Cập nhật màu chữ cho dễ đọc
                text_label = box.children[0]  # Lấy Label bên trong
                if state == "occupied" or state == "available":
                    text_label.color = (1, 1, 1, 1)  # Chữ trắng
                else:
                    text_label.color = (0, 0, 0, 1)  # Chữ đen

        except Exception as e:
            print(f"Error updating UI: {e}")
            self.label_ten_bai.text = "Lỗi cập nhật UI"

    # --- API Call Functions ---

    def handle_tra_cuu(self, instance):
        """Handles the 'Tra cứu' button press."""
        bien_so = self.input_bien_so.text.strip().upper()
        if not bien_so:
            self.show_history_message("Vui lòng nhập biển số xe.", "red")
            return

        full_api_url = f"{API_HISTORY_URL_BASE}{bien_so}"
        print(f"Calling API: {full_api_url}")

        self.show_history_message("Đang tải...", "blue")

        # Call the API using Kivy's built-in UrlRequest
        UrlRequest(
            full_api_url,
            on_success=self.on_api_success,
            on_failure=self.on_api_failure,
            on_error=self.on_api_error,
            timeout=10  # Thêm timeout 10 giây
        )

    def on_api_success(self, request, result):
        """Called when the API call is successful (2xx status)."""
        print(f"API Success: {result}")
        self.history_layout.clear_widgets()  # Clear "Đang tải..."

        # 'result' is already parsed as a list/dict (JSON)
        if not result:
            self.show_history_message("Không tìm thấy lịch sử cho biển số này.", "blue")
            return

        try:
            # result.reverse()
            for item in result:
                item_layout = self.create_history_item(item)
                self.history_layout.add_widget(item_layout)
        except Exception as e:
            print(f"Error parsing API result: {e}")
            self.show_history_message("Lỗi xử lý dữ liệu API.", "red")

    def on_api_failure(self, request, error_result):
        """Called on API failure (non-2xx status)."""
        print(f"API Failure: {error_result}")
        self.show_history_message(f"Lỗi máy chủ API: {error_result}", "red")

    def on_api_error(self, request, error):
        """Called on network error (e.g., no connection)."""
        print(f"API Network Error: {error}")
        self.show_history_message(f"Lỗi mạng: Không thể kết nối API.\n(Kiểm tra URL và kết nối internet)", "red")

    def show_history_message(self, text, msg_type=""):
        """Helper to show a message in the history list area."""
        self.history_layout.clear_widgets()
        color = (0, 0, 0, 1)
        if msg_type == "red":
            color = (0.8, 0, 0, 1)
        elif msg_type == "blue":
            color = (0.1, 0.1, 0.8, 1)

        message_label = Label(text=text, font_size=dp(16), color=color, halign='center')
        self.history_layout.add_widget(message_label)

    # --- UI Creation ---

    def create_dashboard_tab(self):
        """Create the UI for the dashboard tab."""
        # Layout chính: BoxLayout dọc, cuộn được
        root_layout = ScrollView(size_hint=(1, 1))
        main_layout = BoxLayout(
            orientation='vertical',
            padding=dp(15),
            spacing=dp(15),
            size_hint_y=None
        )
        main_layout.bind(minimum_height=main_layout.setter('height'))

        # --- Thẻ 1: Thông tin chung ---
        card_info = InfoCard()
        card_info.add_widget(
            Label(text='Thông tin chung', font_size=dp(18), bold=True, color=(0, 0, 0, 1), size_hint_y=None,
                  height=dp(50)))
        info_grid = GridLayout(cols=2, spacing=(dp(10),dp(40)), size_hint_y=None)
        info_grid.bind(minimum_height=info_grid.setter('height'))

        self.label_ten_bai = self.create_value_label(is_highlight=True)
        self.label_dia_chi = self.create_value_label()

        info_grid.add_widget(self.create_key_label('Tên bãi:'))
        info_grid.add_widget(self.label_ten_bai)
        info_grid.add_widget(self.create_key_label('Địa chỉ:'))
        info_grid.add_widget(self.label_dia_chi)
        card_info.add_widget(info_grid)
        main_layout.add_widget(card_info)

        # --- Thẻ 2: Trạng thái ---
        card_status = InfoCard()
        card_status.add_widget(
            Label(text='Trạng thái', font_size=dp(18), bold=True, color=(0, 0, 0, 1), size_hint_y=None, height=dp(50)))
        status_grid = GridLayout(cols=2, spacing=(dp(10),dp(40)), size_hint_y=None)
        status_grid.bind(minimum_height=status_grid.setter('height'))

        self.label_tong_slot = self.create_value_label()
        self.label_slot_trong = self.create_value_label(is_highlight=True,
                                                        color=get_color_from_hex('#22c55e'))  # Màu xanh lá
        self.label_nhiet_do = self.create_value_label()
        self.label_do_am = self.create_value_label()

        status_grid.add_widget(self.create_key_label('Tổng slot:'))
        status_grid.add_widget(self.label_tong_slot)
        status_grid.add_widget(self.create_key_label('Slot trống:'))
        status_grid.add_widget(self.label_slot_trong)
        status_grid.add_widget(self.create_key_label('Nhiệt độ:'))
        status_grid.add_widget(self.label_nhiet_do)
        status_grid.add_widget(self.create_key_label('Độ ẩm:'))
        status_grid.add_widget(self.label_do_am)
        card_status.add_widget(status_grid)
        main_layout.add_widget(card_status)

        # --- Thẻ 3: Sơ đồ chỗ đỗ ---
        card_slots = InfoCard()
        card_slots.add_widget(
            Label(text='Sơ đồ chỗ đỗ', font_size=dp(18), bold=True, color=(0, 0, 0, 1), size_hint_y=None,
                  height=dp(25)))

        self.slots_layout = GridLayout(cols=4, spacing=dp(10), size_hint_y=None)
        self.slots_layout.bind(minimum_height=self.slots_layout.setter('height'))

        self.slot_widgets = {}
        for i in range(1, 5):
            slot_box = BoxLayout(
                size_hint=(None, None),
                size=(dp(70), dp(70))  # Kích thước ô slot
            )

            with slot_box.canvas.before:
                color_instr = Color(0.8, 0.8, 0.8, 1)  # Màu xám (chưa biết)
                rect = RoundedRectangle(
                    pos=slot_box.pos,
                    size=slot_box.size,
                    radius=[dp(8)]  # Bo góc cho ô slot
                )

            def bind_rect(slot_box, rect):
                slot_box.bind(
                    pos=lambda instance, value: setattr(rect, 'pos', instance.pos),
                    size=lambda instance, value: setattr(rect, 'size', instance.size)
                )

            bind_rect(slot_box, rect)

            label = Label(text=f"S{i}", color=(0, 0, 0, 1), bold=True, font_size=dp(18))
            slot_box.add_widget(label)
            self.slots_layout.add_widget(slot_box)
            self.slot_widgets[f"s{i}"] = (slot_box, rect, color_instr)

        card_slots.add_widget(self.slots_layout)
        main_layout.add_widget(card_slots)

        root_layout.add_widget(main_layout)
        return root_layout

    def create_history_tab(self):
        """Create the UI for the history lookup tab."""
        main_layout = BoxLayout(orientation='vertical', padding=dp(15), spacing=dp(15))

        # --- Thẻ tìm kiếm ---
        search_card = InfoCard(size_hint_y=None)
        top_bar = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(44), spacing=dp(10))

        self.input_bien_so = TextInput(
            hint_text='Nhập biển số xe', multiline=False, size_hint_x=0.7, font_size=dp(16)
        )
        search_button = Button(
            text='Tra cứu', size_hint_x=0.3, font_size=dp(16),
            background_color=get_color_from_hex('#3b82f6'), color=(1, 1, 1, 1),
            background_normal='', # Bỏ background mặc định
        )
        # Thêm bo góc cho nút
        search_button.background_disabled_normal = search_button.background_normal
        with search_button.canvas.before:
            Color(rgb=get_color_from_hex('#3b82f6'))
            search_button.rect = RoundedRectangle(
                pos=search_button.pos,
                size=search_button.size,
                radius=[dp(8)]
            )
        search_button.bind(pos=lambda *args: setattr(search_button.rect, 'pos', search_button.pos),
                           size=lambda *args: setattr(search_button.rect, 'size', search_button.size))

        search_button.bind(on_press=self.handle_tra_cuu)

        top_bar.add_widget(self.input_bien_so)
        top_bar.add_widget(search_button)
        search_card.add_widget(top_bar)
        main_layout.add_widget(search_card)
        # --- Hết thẻ tìm kiếm ---

        # Khu vực kết quả
        scroll_view = ScrollView(size_hint=(1, 1))
        self.history_layout = GridLayout(cols=1, spacing=dp(10), size_hint_y=None) # Thêm spacing
        self.history_layout.bind(minimum_height=self.history_layout.setter('height'))
        scroll_view.add_widget(self.history_layout)
        main_layout.add_widget(scroll_view)

        return main_layout

    def create_key_label(self, text):
        label = Label(
            text=text, halign='left', valign='top', font_size=dp(16),
            color=(0.3, 0.3, 0.3, 1), size_hint_x=0.4
        )

        # --- THÊM DÒNG NÀY ĐỂ SỬA CANH LỀ ---
        # Bắt buộc phải có text_size để valign hoạt động
        label.bind(
            width=lambda instance, value: setattr(label, 'text_size', (value, None))
        )
        # ------------------------------------

        return label

    def create_value_label(self, is_highlight=False, color=None):
        if color is None:
            color = (0.1, 0.1, 0.1, 1)
        font_size = dp(20) if is_highlight else dp(16)

        label = Label(
            text='Đang chờ dữ liệu...', # <-- Thay đổi text mặc định
            halign='left', valign='top', font_size=font_size,
            bold=is_highlight, color=color, size_hint_x=0.6
        )
        label.bind(
            width=lambda instance, value: setattr(label, 'text_size', (value, None))
        )
        return label

    # def create_history_item(self, item_data):
    #     """Create a widget for a single history item."""
    #     # Mỗi item là một InfoCard
    #     item_card = InfoCard(size_hint_y=None)
    #     item_card.padding = dp(12)  # Padding nhỏ hơn
    #     item_card.spacing = dp(4)
    #
    #     # Xóa canvas vẽ đường kẻ (không cần nữa)
    #     # with item_layout.canvas.before: ...
    #     # item_layout.bind(pos=update_rect, size=update_rect)
    #
    #     item_card.add_widget(
    #         Label(
    #             text=f"Vào: {item_data.get('vao', 'N/A')}",
    #             halign='left', font_size=dp(14), color=(0.3, 0.3, 0.3, 1),  # Màu xám
    #             size_hint_y=None, height=dp(20)
    #         )
    #     )
    #     item_card.add_widget(
    #         Label(
    #             text=f"Ra: {item_data.get('ra', 'N/A')}",
    #             halign='left', font_size=dp(14), color=(0.3, 0.3, 0.3, 1),  # Màu xám
    #             size_hint_y=None, height=dp(20)
    #         )
    #     )
    #     item_card.add_widget(
    #         Label(
    #             text=f"Chi phí: {item_data.get('gia', 'N/A')}",
    #             halign='left', font_size=dp(16), bold=True,
    #             color=get_color_from_hex('#16a34a'),
    #             size_hint_y=None, height=dp(25)
    #         )
    #     )
    #
    #     # Căn chỉnh text_size cho các Label
    #     for widget in item_card.children:
    #         if isinstance(widget, Label):
    #             widget.bind(width=lambda instance, value: setattr(instance, 'text_size', (value, None)))
    #
    #     return item_card
    def create_history_item(self, item_data):
        """Create a widget for a single history item."""
        item_card = InfoCard(size_hint_y=None)
        item_card.padding = dp(12)
        item_card.spacing = dp(4)

        time_in = item_data.get('time_in', 'N/A')
        time_out = item_data.get('time_out', 'Đang gửi')
        slot_number = item_data.get('slot_number', 'N/A')
        lot_id = item_data.get('lot_id', 'N/A')

        item_card.add_widget(
            Label(
                text=f"Biển số: {item_data.get('license_plate', 'N/A')}",
                halign='left', font_size=dp(16), bold=True,
                color=(0, 0, 0, 1), size_hint_y=None, height=dp(25)
            )
        )
        item_card.add_widget(
            Label(
                text=f"Bãi: {lot_id} - Slot: {slot_number}",
                halign='left', font_size=dp(14), color=(0.3, 0.3, 0.3, 1),
                size_hint_y=None, height=dp(20)
            )
        )
        item_card.add_widget(
            Label(
                text=f"Vào: {time_in}",
                halign='left', font_size=dp(14), color=(0.3, 0.3, 0.3, 1),
                size_hint_y=None, height=dp(20)
            )
        )
        item_card.add_widget(
            Label(
                text=f"Ra: {time_out}",
                halign='left', font_size=dp(14), color=(0.3, 0.3, 0.3, 1),
                size_hint_y=None, height=dp(20)
            )
        )

        # Căn chỉnh text_size cho các Label
        for widget in item_card.children:
            if isinstance(widget, Label):
                widget.bind(width=lambda instance, value: setattr(instance, 'text_size', (value, None)))

        return item_card


# --- Run the App ---
if __name__ == '__main__':
    ParkingApp().run()




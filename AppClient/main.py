import json
import ssl
import paho.mqtt.client as mqtt
from datetime import datetime

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.clock import Clock
from kivy.metrics import dp, sp
from kivy.utils import get_color_from_hex
from kivy.core.window import Window
from kivy.network.urlrequest import UrlRequest
from kivy.graphics import Color, RoundedRectangle

MQTT_BROKER_HOST = "YOUR_HOST"
MQTT_BROKER_PORT = "YOUR_PORT"
MQTT_TOPIC = "YOUR_TOPIC"
MQTT_USERNAME = "YOUR_USERNAME"
MQTT_PASSWORD = "YOUR_PASSWORD"

API_HISTORY_URL_BASE = "YOUR_API"

Window.clearcolor = (0.95, 0.95, 0.95, 1)

class InfoCard(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.padding = dp(14)
        self.spacing = dp(8)
        self.size_hint_x = 1
        self.size_hint_y = None

        with self.canvas.before:
            Color(1, 1, 1, 1)
            self.rect = RoundedRectangle(
                pos=self.pos,
                size=self.size,
                radius=[dp(12)]
            )

        self.bind(pos=self._update_canvas, size=self._update_canvas)
        self.bind(minimum_height=self.setter("height"))

    def _update_canvas(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size

class ParkingApp(App):

    def format_time(self, iso_time):
        try:
            dt = datetime.fromisoformat(str(iso_time).replace("Z", "+00:00"))
            return dt.strftime("%d/%m/%Y - %H:%M")
        except Exception:
            return str(iso_time)

    def wrap_label(self, lbl: Label):
        lbl.bind(
            size=lambda inst, val:
                setattr(inst, "text_size", (inst.width, None))
        )
        return lbl

    def build(self):
        self.tab_panel = TabbedPanel(do_default_tab=False)
        self.tab_panel.background_color = (1, 1, 1, 1)

        self.tab_dashboard = TabbedPanelItem(text="Dashboard")
        self.tab_dashboard.content = self.create_dashboard_tab()
        self.tab_panel.add_widget(self.tab_dashboard)

        self.tab_history = TabbedPanelItem(text="History")
        self.tab_history.content = self.create_history_tab()
        self.tab_panel.add_widget(self.tab_history)

        Window.bind(on_resize=self.on_resize)
        return self.tab_panel

    def on_start(self):
        try:
            self.mqtt_client = mqtt.Client()
            self.mqtt_client.on_connect = self.on_mqtt_connect
            self.mqtt_client.on_message = self.on_mqtt_message
            self.mqtt_client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)

            self.mqtt_client.tls_set(
                ca_certs="ca.crt",
                certfile=None,
                keyfile=None,
                tls_version=ssl.PROTOCOL_TLSv1_2
            )

            self.mqtt_client.connect_async(MQTT_BROKER_HOST, MQTT_BROKER_PORT, 60)
            self.mqtt_client.loop_start()
            self.set_dashboard_status("Connecting MQTT...", "blue")
        except Exception as e:
            self.set_dashboard_status(f"Error connected MQTT:\n{e}", "red")

    def on_stop(self):
        if hasattr(self, "mqtt_client"):
            self.mqtt_client.loop_stop()
            self.mqtt_client.disconnect()

    # --------- MQTT callbacks ---------
    def on_mqtt_connect(self, client, userdata, flags, rc):
        if rc == 0:
            client.subscribe(MQTT_TOPIC)
            Clock.schedule_once(lambda dt: self.set_dashboard_status("Connected! Loading...", "green"))
        else:
            Clock.schedule_once(lambda dt: self.set_dashboard_status(f"Error connected MQTT: {rc}", "red"))

    def on_mqtt_message(self, client, userdata, msg):
        try:
            payload = msg.payload.decode("utf-8")
            data = json.loads(payload)
            Clock.schedule_once(lambda dt: self.update_dashboard(data))
        except Exception as e:
            Clock.schedule_once(lambda dt: self.set_dashboard_status(f"Error processed message:\n{e}", "red"))

    # --------- Dashboard updates ---------
    def set_dashboard_status(self, text, status_type=""):
        color = (0, 0, 0, 1)
        if status_type == "green":
            color = (0, 0.55, 0, 1)
        elif status_type == "red":
            color = (0.85, 0, 0, 1)
        elif status_type == "blue":
            color = (0.1, 0.1, 0.85, 1)

        self.label_ten_bai.text = text
        self.label_ten_bai.color = color

    def update_dashboard(self, data):
        try:
            self.label_ten_bai.text = data.get("parkingLot", "N/A")
            self.label_ten_bai.color = (0, 0, 0, 1)
            self.label_dia_chi.text = data.get("address", "N/A")
            self.label_tong_slot.text = str(data.get("slot", "N/A"))
            self.label_nhiet_do.text = f"{data.get('temperature', 'N/A')} °C"
            self.label_do_am.text = f"{data.get('humidity', 'N/A')} %"

            status = (data.get("status", {}) or {})
            available_count = sum(1 for v in status.values() if v == "available")
            self.label_slot_trong.text = str(available_count)

            for key, (box, rect, color_instr, text_label) in self.slot_widgets.items():
                state = status.get(key, "unknown")
                if state == "occupied":
                    color_instr.rgba = get_color_from_hex("#ef4444")
                    text_label.color = (1, 1, 1, 1)
                elif state == "available":
                    color_instr.rgba = get_color_from_hex("#22c55e")
                    text_label.color = (1, 1, 1, 1)
                else:
                    color_instr.rgba = get_color_from_hex("#9ca3af")
                    text_label.color = (0, 0, 0, 1)

        except Exception:
            self.label_ten_bai.text = "Error UI!"

    # --------- API ---------
    def handle_tra_cuu(self, instance):
        bien_so = self.input_bien_so.text.strip().upper()
        if not bien_so:
            self.show_history_message("Enter your license plate.", "red")
            return

        full_api_url = f"{API_HISTORY_URL_BASE}{bien_so}"
        self.show_history_message("Loading...", "blue")

        UrlRequest(
            full_api_url,
            on_success=self.on_api_success,
            on_failure=self.on_api_failure,
            on_error=self.on_api_error,
            timeout=10
        )

    def on_api_success(self, request, result):
        self.history_layout.clear_widgets()
        if not result:
            self.show_history_message("Nothing !!!", "blue")
            return
        try:
            for item in result:
                self.history_layout.add_widget(self.create_history_item(item))
        except Exception:
            self.show_history_message("Error processed data!", "red")

    def on_api_failure(self, request, error_result):
        self.show_history_message("Error API server!", "red")

    def on_api_error(self, request, error):
        self.show_history_message("Error Network!", "red")

    def show_history_message(self, text, msg_type=""):
        self.history_layout.clear_widgets()
        color = (0, 0, 0, 1)
        if msg_type == "red":
            color = (0.85, 0, 0, 1)
        elif msg_type == "blue":
            color = (0.1, 0.1, 0.85, 1)

        lbl = Label(text=text, font_size=sp(15), color=color, halign="center",
                    valign="middle", size_hint_y=None, height=dp(30))
        self.wrap_label(lbl)
        self.history_layout.add_widget(lbl)

    def create_dashboard_tab(self):
        root_scroll = ScrollView(size_hint=(1, 1))

        main_layout = BoxLayout(
            orientation="vertical",
            padding=dp(14),
            spacing=dp(14),
            size_hint_y=None
        )
        main_layout.bind(minimum_height=main_layout.setter("height"))

        # --- Card 1: General ---
        card_info = InfoCard()
        title = Label(text="General", font_size=sp(18), bold=True, color=(0, 0, 0, 1),
                      size_hint_y=None, height=dp(36))
        self.wrap_label(title)
        card_info.add_widget(title)

        info_grid = GridLayout(cols=2, spacing=(dp(8), dp(12)), size_hint_y=None)
        info_grid.bind(minimum_height=info_grid.setter("height"))

        self.label_ten_bai = self.create_value_label(is_highlight=True)
        self.label_dia_chi = self.create_value_label()

        info_grid.add_widget(self.create_key_label("Parking Lot:"))
        info_grid.add_widget(self.label_ten_bai)
        info_grid.add_widget(self.create_key_label("Address:"))
        info_grid.add_widget(self.label_dia_chi)

        card_info.add_widget(info_grid)
        main_layout.add_widget(card_info)

        # --- Card 2: Status ---
        card_status = InfoCard()
        title2 = Label(text="Status", font_size=sp(18), bold=True, color=(0, 0, 0, 1),
                       size_hint_y=None, height=dp(36))
        self.wrap_label(title2)
        card_status.add_widget(title2)

        status_grid = GridLayout(cols=2, spacing=(dp(8), dp(12)), size_hint_y=None)
        status_grid.bind(minimum_height=status_grid.setter("height"))

        self.label_tong_slot = self.create_value_label()
        self.label_slot_trong = self.create_value_label(is_highlight=True, color=get_color_from_hex("#22c55e"))
        self.label_nhiet_do = self.create_value_label()
        self.label_do_am = self.create_value_label()

        status_grid.add_widget(self.create_key_label("Slot:"))
        status_grid.add_widget(self.label_tong_slot)
        status_grid.add_widget(self.create_key_label("Available Slot:"))
        status_grid.add_widget(self.label_slot_trong)
        status_grid.add_widget(self.create_key_label("Temperature:"))
        status_grid.add_widget(self.label_nhiet_do)
        status_grid.add_widget(self.create_key_label("Humidity:"))
        status_grid.add_widget(self.label_do_am)

        card_status.add_widget(status_grid)
        main_layout.add_widget(card_status)

        # --- Card 3: Map ---
        card_slots = InfoCard()
        title3 = Label(text="Map", font_size=sp(18), bold=True, color=(0, 0, 0, 1),
                       size_hint_y=None, height=dp(28))
        self.wrap_label(title3)
        card_slots.add_widget(title3)

        cols = 2 if Window.width < 600 else 4
        self.slots_layout = GridLayout(cols=cols, spacing=dp(10), size_hint_y=None)
        self.slots_layout.bind(minimum_height=self.slots_layout.setter("height"))

        self.slot_widgets = {}
        for i in range(1, 5):
            slot_box = BoxLayout(
                size_hint=(1, None),
                height=dp(80) if Window.width < 600 else dp(70),
                padding=dp(4)
            )
            with slot_box.canvas.before:
                color_instr = Color(0.8, 0.8, 0.8, 1)
                rect = RoundedRectangle(pos=slot_box.pos, size=slot_box.size, radius=[dp(8)])

            slot_box.bind(pos=lambda inst, v, r=rect: setattr(r, "pos", inst.pos))
            slot_box.bind(size=lambda inst, v, r=rect: setattr(r, "size", inst.size))

            label = Label(text=f"S{i}", bold=True, font_size=sp(16), color=(0, 0, 0, 1))
            self.wrap_label(label)
            slot_box.add_widget(label)

            self.slots_layout.add_widget(slot_box)
            self.slot_widgets[f"s{i}"] = (slot_box, rect, color_instr, label)

        card_slots.add_widget(self.slots_layout)
        main_layout.add_widget(card_slots)

        root_scroll.add_widget(main_layout)
        return root_scroll

    def create_history_tab(self):
        main_layout = BoxLayout(orientation="vertical", padding=dp(14), spacing=dp(12))

        search_card = InfoCard(size_hint_y=None)
        top_bar = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(46), spacing=dp(8))

        self.input_bien_so = TextInput(
            hint_text="Enter license plate",
            multiline=False,
            size_hint_x=0.65,
            font_size=sp(15),
            padding=(dp(10), dp(10))
        )

        search_button = Button(
            text="Search",
            size_hint_x=0.35,
            font_size=sp(15),
            background_normal="",
            background_color=get_color_from_hex("#3b82f6"),
            color=(1, 1, 1, 1)
        )

        search_button.background_disabled_normal = search_button.background_normal
        with search_button.canvas.before:
            Color(rgb=get_color_from_hex("#3b82f6"))
            search_button.rect = RoundedRectangle(pos=search_button.pos, size=search_button.size, radius=[dp(8)])
        search_button.bind(pos=lambda *a: setattr(search_button.rect, "pos", search_button.pos))
        search_button.bind(size=lambda *a: setattr(search_button.rect, "size", search_button.size))

        search_button.bind(on_press=self.handle_tra_cuu)

        top_bar.add_widget(self.input_bien_so)
        top_bar.add_widget(search_button)
        search_card.add_widget(top_bar)
        main_layout.add_widget(search_card)

        scroll_view = ScrollView(size_hint=(1, 1))
        self.history_layout = GridLayout(cols=1, spacing=dp(10), size_hint_y=None)
        self.history_layout.bind(minimum_height=self.history_layout.setter("height"))
        scroll_view.add_widget(self.history_layout)
        main_layout.add_widget(scroll_view)

        return main_layout

    def create_key_label(self, text):
        lbl = Label(
            text=text,
            font_size=sp(15),
            color=(0.35, 0.35, 0.35, 1),
            halign="left",
            valign="middle",
            size_hint_x=0.38,
            size_hint_y=None,
            height=dp(24)
        )
        return self.wrap_label(lbl)

    def create_value_label(self, is_highlight=False, color=None):
        if color is None:
            color = (0.1, 0.1, 0.1, 1)
        font_size = sp(18) if is_highlight else sp(15)

        lbl = Label(
            text="Loading...",
            font_size=font_size,
            bold=is_highlight,
            color=color,
            halign="left",
            valign="middle",
            size_hint_x=0.62,
            size_hint_y=None,
            height=dp(24)
        )
        return self.wrap_label(lbl)

    def create_history_item(self, item_data):
        item_card = InfoCard(size_hint_y=None)
        item_card.padding = dp(12)
        item_card.spacing = dp(4)

        raw_in = item_data.get("time_in", "N/A")
        raw_out = item_data.get("time_out", "Sending!")

        time_in = self.format_time(raw_in) if raw_in != "N/A" else "N/A"
        time_out = self.format_time(raw_out) if raw_out != "Sending" else "Sending"

        slot_number = item_data.get("slot_number", "N/A")
        lot_id = item_data.get("lot_id", "N/A")

        title = Label(
            text=f"License plate: {item_data.get('license_plate', 'N/A')}",
            font_size=sp(16),
            bold=True,
            color=(0, 0, 0, 1),
            halign="left",
            size_hint_y=None,
            height=dp(26)
        )
        self.wrap_label(title)
        item_card.add_widget(title)

        sub = Label(
            text=f"CodePL: {lot_id} - CodeS: {slot_number}",
            font_size=sp(14),
            color=(0.35, 0.35, 0.35, 1),
            halign="left",
            size_hint_y=None,
            height=dp(20)
        )
        self.wrap_label(sub)
        item_card.add_widget(sub)

        lin = Label(
            text=f"Time in: {time_in}",
            font_size=sp(14),
            color=(0.35, 0.35, 0.35, 1),
            halign="left",
            size_hint_y=None,
            height=dp(20)
        )
        self.wrap_label(lin)
        item_card.add_widget(lin)

        lout = Label(
            text=f"Time out: {time_out}",
            font_size=sp(14),
            color=(0.35, 0.35, 0.35, 1),
            halign="left",
            size_hint_y=None,
            height=dp(20)
        )
        self.wrap_label(lout)
        item_card.add_widget(lout)

        return item_card

    # --------- Responsive reflow ---------
    def on_resize(self, window, width, height):
        if hasattr(self, "slots_layout"):
            self.slots_layout.cols = 2 if width < 600 else 4
        if hasattr(self, "slot_widgets"):
            target_h = dp(80) if width < 600 else dp(70)
            for _, (slot_box, _, _, _) in self.slot_widgets.items():
                slot_box.height = target_h


if __name__ == "__main__":
    ParkingApp().run()

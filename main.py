from kivy.app import App
from kivy.clock import Clock
from kivy.core.text import Label as CoreLabel
from kivy.graphics import Color, Rectangle
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput
from kivy.uix.slider import Slider
from kivy.uix.popup import Popup
from kivy.utils import get_color_from_hex
import os
import re

MOODS = {
    "Calm": {"bg": "#1e2a38", "fg": "#f4ead5", "accent": "#8fb8de"},
    "Dark": {"bg": "#0d0d0d", "fg": "#d9d9d9", "accent": "#7a1f1f"},
    "Romantic": {"bg": "#3b1f2b", "fg": "#ffe9f0", "accent": "#e89ab5"},
    "Rain": {"bg": "#202b2f", "fg": "#dfe9ec", "accent": "#6fa3b8"},
}
STANZA_COLORS = ["#1e2a38", "#2b2f3d", "#2e2433", "#1f2e2e"]


class PoetryReelMaker(App):
    def build(self):
        self.title = "Bengali Poetry Reel Maker"
        self.stanzas = []
        self.playing = False
        self.stanza_index = 0
        self.char_index = 0
        self.event = None
        self.mood_name = "Calm"
        self.speed_ms = 40
        self.hold_ms = 1800

        root = BoxLayout(orientation="vertical", padding=dp(12), spacing=dp(8))
        root.add_widget(Label(text="[b]Bengali Poetry Reel Maker[/b]", markup=True,
                              size_hint_y=None, height=dp(38), font_size="20sp"))

        settings = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(6))
        settings.add_widget(Label(text="Mood", size_hint_x=None, width=dp(48)))
        self.mood_spinner = Spinner(text="Calm", values=list(MOODS.keys()), size_hint_x=1)
        self.mood_spinner.bind(text=self.on_mood)
        settings.add_widget(self.mood_spinner)
        root.add_widget(settings)

        root.add_widget(Label(text="কবিতা লিখুন (প্রতিটি স্তবকের মাঝে একটি খালি লাইন দিন):",
                              size_hint_y=None, height=dp(30), halign="left"))
        self.poem_input = TextInput(hint_text="এখানে আপনার কবিতা পেস্ট করুন…",
                                    multiline=True, size_hint_y=0.34,
                                    font_size="17sp", padding=dp(10))
        root.add_widget(self.poem_input)

        controls = BoxLayout(size_hint_y=None, height=dp(52), spacing=dp(8))
        self.speed_label = Label(text="Speed: 40 ms", size_hint_x=0.42)
        controls.add_widget(self.speed_label)
        self.speed_slider = Slider(min=10, max=200, value=40)
        self.speed_slider.bind(value=self.on_speed)
        controls.add_widget(self.speed_slider)
        root.add_widget(controls)

        hold_controls = BoxLayout(size_hint_y=None, height=dp(52), spacing=dp(8))
        self.hold_label = Label(text="Hold: 1.8 s", size_hint_x=0.42)
        hold_controls.add_widget(self.hold_label)
        self.hold_slider = Slider(min=0.5, max=10, value=1.8)
        self.hold_slider.bind(value=self.on_hold)
        hold_controls.add_widget(self.hold_slider)
        root.add_widget(hold_controls)

        self.preview = Label(text="আপনার কবিতার প্রিভিউ এখানে দেখা যাবে",
                             font_size="23sp", halign="center", valign="middle",
                             size_hint_y=1, color=get_color_from_hex(MOODS["Calm"]["fg"]))
        self.preview.bind(size=lambda inst, val: setattr(inst, "text_size", val))
        self.preview_bg = BoxLayout(size_hint_y=1)
        with self.preview_bg.canvas.before:
            self.bg_color = Color(*get_color_from_hex(MOODS["Calm"]["bg"]))
            self.bg_rect = Rectangle(pos=self.preview_bg.pos, size=self.preview_bg.size)
        self.preview_bg.bind(pos=self.update_bg_rect, size=self.update_bg_rect)
        self.preview_bg.add_widget(self.preview)
        root.add_widget(self.preview_bg)

        buttons = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(8))
        play_btn = Button(text="▶ Play")
        play_btn.bind(on_release=self.play)
        stop_btn = Button(text="■ Stop")
        stop_btn.bind(on_release=self.stop)
        export_btn = Button(text="Export PNGs")
        export_btn.bind(on_release=self.export_pngs)
        buttons.add_widget(play_btn)
        buttons.add_widget(stop_btn)
        buttons.add_widget(export_btn)
        root.add_widget(buttons)

        self.status = Label(text="Ready", size_hint_y=None, height=dp(26))
        root.add_widget(self.status)
        return root

    def update_bg_rect(self, *_):
        self.bg_rect.pos = self.preview_bg.pos
        self.bg_rect.size = self.preview_bg.size

    def on_mood(self, _spinner, value):
        self.mood_name = value
        mood = MOODS[value]
        self.bg_color.rgba = get_color_from_hex(mood["bg"])
        self.preview.color = get_color_from_hex(mood["fg"])

    def on_speed(self, _slider, value):
        self.speed_ms = int(value)
        self.speed_label.text = f"Speed: {self.speed_ms} ms"

    def on_hold(self, _slider, value):
        self.hold_ms = int(value * 1000)
        self.hold_label.text = f"Hold: {value:.1f} s"

    def parse_stanzas(self):
        raw = self.poem_input.text.strip()
        return [part.strip() for part in re.split(r"\n\s*\n", raw) if part.strip()]

    def play(self, *_):
        self.stop()
        self.stanzas = self.parse_stanzas()
        if not self.stanzas:
            self.show_message("কবিতা খালি", "আগে একটি কবিতা পেস্ট করুন।")
            return
        self.playing = True
        self.stanza_index = 0
        self.show_stanza()

    def stop(self, *_):
        self.playing = False
        if self.event is not None:
            self.event.cancel()
            self.event = None
        self.status.text = "Stopped"

    def show_stanza(self, *_):
        if not self.playing:
            return
        if self.stanza_index >= len(self.stanzas):
            self.playing = False
            self.status.text = "Done"
            return
        self.char_index = 0
        stanza = self.stanzas[self.stanza_index]
        self.status.text = f"Stanza {self.stanza_index + 1} of {len(self.stanzas)}"
        self.preview.text = ""
        self.preview_bg.canvas.before.clear()
        with self.preview_bg.canvas.before:
            Color(*get_color_from_hex(STANZA_COLORS[self.stanza_index % len(STANZA_COLORS)]))
            self.bg_rect = Rectangle(pos=self.preview_bg.pos, size=self.preview_bg.size)
        self.type_next()

    def type_next(self, *_):
        if not self.playing:
            return
        stanza = self.stanzas[self.stanza_index]
        self.char_index += 1
        self.preview.text = stanza[:self.char_index]
        if self.char_index < len(stanza):
            self.event = Clock.schedule_once(self.type_next, self.speed_ms / 1000.0)
        else:
            self.event = Clock.schedule_once(self.next_stanza, self.hold_ms / 1000.0)

    def next_stanza(self, *_):
        self.stanza_index += 1
        self.show_stanza()

    def export_pngs(self, *_):
        stanzas = self.parse_stanzas()
        if not stanzas:
            self.show_message("কবিতা খালি", "PNG Export করার আগে কবিতা পেস্ট করুন।")
            return
        export_dir = os.path.join(self.user_data_dir, "exports")
        os.makedirs(export_dir, exist_ok=True)
        mood = MOODS[self.mood_name]
        for index, stanza in enumerate(stanzas, start=1):
            label = CoreLabel(text=stanza, font_size=42,
                              color=get_color_from_hex(mood["fg"]),
                              text_size=(1000, None), halign="center",
                              valign="middle", font_name="Roboto")
            label.refresh()
            texture = label.texture
            texture.save(os.path.join(export_dir, f"stanza_{index:02d}.png"))
        self.show_message("Export complete", f"{len(stanzas)}টি PNG ফাইল সেভ হয়েছে:\n{export_dir}")

    def show_message(self, title, message):
        box = BoxLayout(orientation="vertical", padding=dp(12), spacing=dp(10))
        box.add_widget(Label(text=message, halign="center"))
        close = Button(text="OK", size_hint_y=None, height=dp(44))
        popup = Popup(title=title, content=box, size_hint=(0.9, 0.42))
        close.bind(on_release=popup.dismiss)
        box.add_widget(close)
        popup.open()


if __name__ == "__main__":
    PoetryReelMaker().run()

# Android build workflow trigger: initial source committed.

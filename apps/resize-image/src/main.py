import os
from PIL import Image
import flet as ft

def resize_image(img_path, output_path, resize_mode, percent=None, width=None, height=None):
    img = Image.open(img_path)
    if resize_mode == "percent":
        w, h = img.size
        new_size = (int(w * percent / 100), int(h * percent / 100))
    else:
        new_size = (width, height)
    resized_img = img.resize(new_size, Image.LANCZOS)
    resized_img.save(output_path)

def main(page: ft.Page):
    page.title = "画像リサイズツール"
    page.window.width = 400  
    page.window.height = 550  
    page.window.min_width = 300
    page.window.min_height = 450
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.update()
    page.scroll = "auto"

    input_folder_field = ft.TextField(label="入力フォルダ", read_only=True)
    output_folder_field = ft.TextField(label="出力フォルダ", read_only=True)
    resize_mode_dropdown = ft.Dropdown(
        label="リサイズ方法",
        options=[
            ft.dropdown.Option("パーセント指定"),
            ft.dropdown.Option("幅と高さを指定")
        ],
        value="パーセント指定",
        on_change=lambda e: update_input_fields()
    )

    percent_field = ft.TextField(label="パーセント（例：50）", keyboard_type=ft.KeyboardType.NUMBER, visible=True, text_align=ft.TextAlign.CENTER)
    width_field = ft.TextField(label="幅", keyboard_type=ft.KeyboardType.NUMBER, visible=False, text_align=ft.TextAlign.CENTER)
    height_field = ft.TextField(label="高さ", keyboard_type=ft.KeyboardType.NUMBER, visible=False, text_align=ft.TextAlign.CENTER)

    result_text = ft.Text()

    def update_input_fields():
        if resize_mode_dropdown.value == "パーセント指定":
            percent_field.visible = True
            width_field.visible = False
            height_field.visible = False
        else:
            percent_field.visible = False
            width_field.visible = True
            height_field.visible = True
        page.update()

    def pick_input_folder(e):
        folder_picker.get_directory_path(dialog_title="入力フォルダを選択")

    def pick_output_folder(e):
        output_picker.get_directory_path(dialog_title="出力フォルダを選択")

    def on_input_folder_selected(e):
        if e.path:
            input_folder_field.value = e.path
            page.update()

    def on_output_folder_selected(e):
        if e.path:
            output_folder_field.value = e.path
            page.update()

    def run_resize(e):
        input_folder = input_folder_field.value
        output_folder = output_folder_field.value
        mode = resize_mode_dropdown.value

        if not input_folder or not output_folder:
            result_text.value = "入力・出力フォルダを選択してください。"
            result_text.color = ft.colors.RED
            page.update()
            return

        try:
            for filename in os.listdir(input_folder):
                if filename.lower().endswith((".jpg", ".jpeg", ".png", ".bmp", ".gif")):
                    input_path = os.path.join(input_folder, filename)
                    output_path = os.path.join(output_folder, filename)

                    if mode == "パーセント指定":
                        percent = int(percent_field.value)
                        resize_image(input_path, output_path, "percent", percent=percent)
                    else:
                        width = int(width_field.value)
                        height = int(height_field.value)
                        resize_image(input_path, output_path, "size", width=width, height=height)

            result_text.value = "画像のリサイズが完了しました。"
            result_text.color = ft.colors.GREEN
        except Exception as ex:
            result_text.value = f"エラー: {ex}"
            result_text.color = ft.colors.RED

        page.update()

    folder_picker = ft.FilePicker(on_result=on_input_folder_selected)
    output_picker = ft.FilePicker(on_result=on_output_folder_selected)
    page.overlay.extend([folder_picker, output_picker])

    page.add(
        ft.Column([
            ft.Text("画像リサイズツール", size=20, weight=ft.FontWeight.BOLD),

            ft.ElevatedButton("入力フォルダを選択", icon=ft.icons.FOLDER_OPEN, on_click=pick_input_folder),
            input_folder_field,

            ft.ElevatedButton("出力フォルダを選択", icon=ft.icons.FOLDER_OPEN, on_click=pick_output_folder),
            output_folder_field,

            resize_mode_dropdown,
            percent_field,
            width_field,
            height_field,

            ft.ElevatedButton("画像をリサイズ", icon=ft.icons.IMAGE, on_click=run_resize),
            result_text
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER)
    )

    update_input_fields()

if __name__ == "__main__":
    ft.app(target=main)

import subprocess
import os


def ui_exporter(ui_in_file, output_dir, output_ui_py_name):

    #ensure that dir exits
    os.makedirs(output_dir, exist_ok=True)

    #construct full path
    output_file_path = os.path.join(output_dir, output_ui_py_name)

    # the commands
    command = [
        'pyuic5',
        '-x',
        ui_in_file,
        '-o',
        output_file_path
    ]

    try:
        # Run the command
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        print("Conversion successful!")
        print(f"Output written to: {output_file_path}")
        print("STDOUT:", result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)

    except FileNotFoundError:
        print("Error: pyuic5 command not found. Is PyQt5 installed and in your PATH?")
    except subprocess.CalledProcessError as e:
        print(f"Error during conversion: {e}")
        print("STDOUT:", e.stdout)
        print("STDERR:", e.stderr)

if __name__=="__main__":
    ui_exporter("../gui/GUSS.ui", '../gui', 'GUSS_ui.py')
    ui_exporter("../gui/dialog.ui", '../gui', 'dialog_ui.py')
    ui_exporter("../gui/error_dialog.ui", '../gui', 'error_dialog_ui.py')
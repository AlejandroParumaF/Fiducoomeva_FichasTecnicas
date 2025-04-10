import time
import pyautogui
from pathlib import Path
from os import environ
from pywinauto.application import Application
import datetime

def find_path(target, start_path=None):
    if start_path is None:
        profile_path = environ.get('USERPROFILE')
        if not profile_path:
            print("Error: Variable de entorno 'USERPROFILE' no encontrada.")
            return None
        start_dir = Path(profile_path)
    else:
        start_dir = Path(start_path)

    if not start_dir.is_dir():
         print(f"Error: La ruta de inicio '{start_dir}' no es un directorio válido.")
         return None
    try:
        for potential_match in start_dir.rglob(target):
            if potential_match.is_file():
                print(f"¡Archivo encontrado!: {potential_match}")
                return potential_match
    except PermissionError:
        print(f"Se encontró un error de permisos durante la búsqueda en '{start_dir}' o subdirectorios.")
    except Exception as e:
        print(f"Ocurrió un error inesperado durante la búsqueda: {e}")

    print(f"Archivo '{target}' no encontrado.")
    return None

def open_sifi():
    path = find_path('SIFI 12C.bat')
    app = Application().start(str(path), timeout=10, wait_for_idle=False)

    find = False
    id = -1

    while not find:
        try:
            app = Application(backend="uia").connect(title_re = ".*Advertencia*")
            id = app.process
            main_dlg = app.window(title='Advertencia de Seguridad')
            find = True
        except:
            continue

    main_dlg.wait('visible')
    pyautogui.press('tab', presses=2, interval=0.5)
    pyautogui.press('space')
    pyautogui.press('enter')

    return id

def login_sifi(pid, us, psw):
    time.sleep(1)
    app = Application(backend="uia").connect(process = pid)
    main_dlg = app.window(title='Sistema de Administracion de Menus.')
    main_dlg.wait('visible')
    time.sleep(1)
    pyautogui.write(us)
    pyautogui.press('enter')
    pyautogui.typewrite(psw)
    pyautogui.press('enter', presses=3, interval=0.5)

def enter_rentability_module():
    pyautogui.press('down', presses=2, interval=1)
    time.sleep(1)
    pyautogui.press('enter')
    time.sleep(0.5)

    for _ in range(3):
        pyautogui.press('down', presses=3, interval=0.2)
        pyautogui.press('enter')

def search_rentability_report(start_fond, end_fond, date):
    pyautogui.write(start_fond)
    pyautogui.press('tab')
    pyautogui.write(date)
    pyautogui.press('tab')
    pyautogui.write(end_fond)
    pyautogui.press('tab')
    pyautogui.write(date)
    pyautogui.press('tab')
    time.sleep(70)

    pyautogui.moveTo(1361, 669, duration=0.2) 
    pyautogui.mouseDown(button='left')
    time.sleep(2)
    pyautogui.mouseUp(button='left')
    time.sleep(0.5)
    pyautogui.click(480, 650, button='left')
    time.sleep(0.5)

def save_rentability_report():
   pyautogui.press('tab', presses=4, interval=0.5)
   pyautogui.press('enter', presses=2, interval=0.5)
   time.sleep(1)

def get_path_rentability_report():
    temp_path = Path("C:/temp")
    if temp_path.exists() and temp_path.is_dir():
        try:
            today = datetime.date.today().strftime("%Y%m%d")
            file_prefix = "SFMCRENT"
            valid_extensions = {".xls", ".xlsx"}
            found_file_path = None

            for item in temp_path.iterdir():
                if item.is_file():
                    filename = item.name
                    extension = item.suffix.lower()
                    if (filename.startswith(file_prefix) and today in filename and extension in valid_extensions):
                        print(f"¡Archivo encontrado!: {item}")
                        found_file_path = item
                        break
                
            if found_file_path:
                print(f"\nRuta completa del archivo encontrado: {found_file_path.resolve()}")
                return found_file_path.resolve()
            
            else:
                print(f"\nNo se encontró ningún archivo que cumpla los criterios")
                return None
        except PermissionError:
            print("Error: No tienes permisos para leer el contenido de la carpeta.")
        except Exception as e:
            print(f"Ocurrió un error al listar el contenido: {e}")
    else:
        print(f"La carpeta '{temp_path}' no existe o no es un directorio.")

def exit_sifi():
    pyautogui.hotkey('alt', 'f4')
    pyautogui.press('left', presses=5)
    pyautogui.hotkey('alt', 'f4')
    pyautogui.hotkey('alt', 'f4')
    pyautogui.press('tab')
    pyautogui.press('enter')

def generate_rentability_report(user, password, date):
    pid = open_sifi()
    login_sifi(pid, user, password)
    time.sleep(5)
    enter_rentability_module()
    search_rentability_report('101', '501', date)
    save_rentability_report()
    exit_sifi()
    return get_path_rentability_report()


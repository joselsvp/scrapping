import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

DRIVER_ROOT = 'C:/Users/josev/Escritorio/chromedriver-win64/chromedriver.exe'
CORREO = 'al049738@uacam.mx'
CONTRASENIA = 'DSA22093'
COORDINACION_FOLDER = 'PROCESAMIENTO'
FOLIO = 'PRC-03'
LOCAL_ROOT = 'E:/PRC-03'

def handle_confirmation(driver):
    try:
        alert = WebDriverWait(driver, 2).until(EC.alert_is_present())
        alert.accept()
        print("Confirmación aceptada automáticamente.")
    except:
        pass

def create_remote_folder(driver, folder_name):
    try:
        print(f"Creando carpeta: {folder_name}")
        folder_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "nombre_carpeta"))
        )
        folder_input.clear()
        folder_input.send_keys(folder_name)

        create_button = driver.find_element(By.CSS_SELECTOR, "a.btn-success")
        create_button.click()

        handle_confirmation(driver)

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.LINK_TEXT, folder_name))
        )
        print(f"Carpeta '{folder_name}' creada exitosamente.")
    except Exception as e:
        print(f"Error al crear la carpeta '{folder_name}': {e}")

def verify_file(driver, file_path):
    try:
        filename = os.path.basename(file_path)
        print(f'Filename: {filename}')

        possible_filenames = [filename, f"*{filename}"]
        
        for name in possible_filenames:
            try:
                file = driver.find_elements(By.LINK_TEXT, name)
                if (len(file) > 0):
                    print(f'Encontrado: {file}')
                    return True
            except:
                continue

        print(f'No se encontró ninguna variante del archivo {filename}')
        return False

    except Exception as e:
        print(f'Error al encontrar el link: {e}')
        return False

def upload_file(driver, file_path):
    try:
        exist_file = verify_file(driver, file_path)
        if exist_file: 
            return

        print(f"Subiendo archivo: {file_path}")
        file_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='file']"))
        )
        file_input.send_keys(file_path)

        wait_for_all_uploads(driver)
        print(f"Archivo '{file_path}' subido exitosamente.")
    except Exception as e:
        print(f"Error al subir el archivo '{file_path}': {e}")

def wait_for_all_uploads(driver, max_wait=18000):
    print("Esperando a que se completen todas las subidas...")
    start_time = time.time()

    while True:
        pending_uploads = driver.find_elements(By.CSS_SELECTOR, ".dz-preview:not(.dz-success)")
        if not pending_uploads:
            print("Todas las subidas se han completado.")
            return True

        for pending in pending_uploads:
            file_name = pending.find_element(By.CSS_SELECTOR, ".dz-filename span").text
            progress = pending.find_element(By.CSS_SELECTOR, ".dz-progress span").get_attribute("style")
            print(f"Archivo pendiente: {file_name}, progreso: {progress}")

        if time.time() - start_time > max_wait:
            print("Archivos que no se subieron:")
            for pending in pending_uploads:
                file_name = pending.find_element(By.CSS_SELECTOR, ".dz-filename span").text
                print(f"  - {file_name}")
            raise TimeoutError("Se agotó el tiempo de espera. Algunos archivos no se subieron correctamente.")

        time.sleep(5)

def replicate_structure(driver, local_path):
    # Navegar primero al directorio FOLIO
    folder_root = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.LINK_TEXT, COORDINACION_FOLDER))
    )
    folder_root.click()

    folio_folder = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.LINK_TEXT, FOLIO))
    )
    folio_folder.click()

    for root, dirs, files in os.walk(local_path):
        relative_path = os.path.relpath(root, local_path).replace("\\", "/")
        if relative_path == ".":
            # Para archivos en la raíz, subirlos directamente al FOLIO
            for file in files:
                file_path = os.path.join(root, file)
                upload_file(driver, file_path)
            continue

        # Crear y navegar la estructura de carpetas
        path_parts = relative_path.split("/")
        current_level = 0
        
        for part in path_parts:
            try:
                create_remote_folder(driver, part)
                folder_link = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.LINK_TEXT, part))
                )
                folder_link.click()
                current_level += 1
            except Exception as e:
                print(f"Error al navegar a la carpeta '{part}': {e}")

        # Subir archivos en la carpeta actual
        for file in files:
            file_path = os.path.join(root, file)
            upload_file(driver, file_path)

        # Regresar al directorio del FOLIO
        for _ in range(current_level):
            driver.back()

# Configuración del WebDriver
service = Service(DRIVER_ROOT)
driver = webdriver.Chrome(service=service)

try:
    # Inicio de sesión
    driver.get("https://repositoriot.inah.gob.mx/arrastrar/index.php")
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "correo")))
    driver.find_element(By.NAME, "correo").send_keys(CORREO)
    driver.find_element(By.NAME, "contrasenia").send_keys(CONTRASENIA)
    driver.find_element(By.NAME, "iniciar").click()

    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "file_upload")))
    print("Inicio de sesión exitoso")

    # Replicar estructura local siempre dentro del FOLIO
    replicate_structure(driver, LOCAL_ROOT)

    print("Estructura replicada exitosamente")

finally:
    driver.quit()
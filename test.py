import sys
from main import main  # Asegúrate de que 'main' es el punto de entrada de tu aplicación

if __name__ == "__main__":
    # Puedes obtener parámetros de la línea de comandos si es necesario
    if len(sys.argv) > 1:
        param = sys.argv[1]
        # Procesa el parámetro aquí si es necesario
        print(f"Parametro recibido: {param}")
    # Ejecuta la aplicación principal
    main()

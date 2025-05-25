from codrone_edu.drone import Drone
import time

# Координаты маршрута (пример — квадрат)
route = [
    (51.127, 71.427),
    (51.128, 71.427),
    (51.128, 71.428),
    (51.127, 71.428),
    (51.127, 71.427)
]

drone = Drone()
drone.pair()
drone.takeoff()

for lat, lon in route:
    # ТВОЯ ЛОГИКА управления дроном (пример: drone.go(...))
    # Сюда можешь вставить реальные команды движения!

    # Записываем координаты в файл для GUI
    with open("drone_position.txt", "w") as f:
        f.write(f"{lat},{lon}")

    time.sleep(2)  # Даем время на перемещение

drone.land()
drone.close()

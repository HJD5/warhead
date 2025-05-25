class Drone:
    def __init__(self, name, model, serial):
        self.name = name
        self.model = model
        self.serial = serial

class Pilot:
    def __init__(self, name, contacts):
        self.name = name
        self.contacts = contacts

class Flight:
    def __init__(self, drone_id, pilot_id, route, status='ожидание'):
        self.drone_id = drone_id
        self.pilot_id = pilot_id
        self.route = route
        self.status = status

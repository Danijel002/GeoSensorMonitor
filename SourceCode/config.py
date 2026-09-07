""" Central configuration for the project """

#MongoDB
MONGO_HOST="localhost"
MONGO_PORT=27017
MONGO_DB="sensor_data"
MONGO_COLLECTION = "readings"

#Serial port (virtual COM used by the Br@y terminal / simulator)
SERIAL_PORT="COM6"
SERIAL_BAUDRATE=9600
SERIAL_TIMEOUT = 1  # seconds

# Map
MAP_CENTER = (44.016521, 21.005859)
MAP_ZOOM = 7
HISTORY_LIMIT = 10  # readings shown in each marker popup
 
# Sensor nodes: id -> (latitude, longitude, label)
NODES = {
    1: (45.254410, 19.842550, "Novi Sad"),
    2: (44.815071, 20.460480, "Belgrade"),
    3: (43.316872, 21.894501, "Niš"),
    4: (45.773979, 19.118759, "Sombor"),
    5: (43.981270, 21.257441, "Jagodina"),
}
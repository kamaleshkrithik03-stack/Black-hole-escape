SCREEN_HEIGHT = 1280
SCREEN_WIDTH = 800
FPS = 60

T_MASS = 1.31 * 10**41 # the mass of a TON 618
S_MASS = 8.54 * 10**36 #sagittarius A* 
G_MASS = 7.2 * 10**30 # smallest observed black hole im not using planck mass cuz thats too small

G = 6.6743 * 10**-11 # gravitational constant according to google

COLOR_BG = (10, 10, 15)
COLOR_GRID = (150, 150, 160)
COLOR_TEXT = (220, 220, 230)
COLOR_SHIP = (50, 150, 255)
COLOR_BH = (0, 0, 0) # it has to be pitch black right
COLOR_ACCRETION = (199, 74, 0) # Orange as thats plasma ig 
COLOR_TRAIL = (100, 120, 180, 100)

LEVELS = {
    1: {
        "name": "Level 1: smallest black hole G3425",
        "mass": G_MASS,
        "event_horizon": 25,
        "description": "smallest blackhole in the universe so if u lose u dont know phy"

    },
    2: {
        "name": "Level 2: Sagittaries A*",
                "mass": S_MASS,
                "event_horizon": 50,
                "description": "This is the supermassive blackhole in the centre of our milkyway"
        
    },
    3: {
        "name": "Level 3: TON 618",
        "mass": T_MASS,
        "event_horizon": 75,
        "description": "biggest baddest black hole as far a ik"

    },

}



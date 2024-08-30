import sdl2
import sdl2.ext

def main():
    sdl2.ext.init()
    window = sdl2.ext.Window("SDL2 Test", size=(1280, 720))
    window.show()

    running = True
    while running:
        events = sdl2.ext.get_events()
        for event in events:
            if event.type == sdl2.SDL_QUIT:
                running = False
        window.refresh()

    sdl2.ext.quit()

if __name__ == "__main__":
    main()

import React, { useEffect, useState } from "react";

import mapboxgl from "mapbox-gl";

import "./style.css";
import { CityPillContainer } from "./city-pill";
import { QueryClient, QueryClientProvider } from "react-query";
import { ControlSidebar } from "./control-sidebar";
import { BlurBackground, WelcomePopup } from "./welcome-popup";
import { InformationIcon } from "./information-icon";
import { type BrightnessContextInt } from "./time-slider";
import { BikeMap } from "./bike";
import { type JSX } from "react/jsx-runtime";
import { GIF_RENDER } from "./gif-generator";

export const BG_WHITE_COLOR = "bg-zinc-50";

export const BrightnessContext = React.createContext<BrightnessContextInt>({
    brightness: 100,
    setBrightness: (_value: number) => {},
});

export const CITY_LOCATION = {
    London: new mapboxgl.LngLat(-81.2453, 42.9849), // London, Canada coordinates
};

export function MapboxGLCanvasBrightnessHack({ brightness }: { brightness: number }) {
    const element1 = [...document.getElementsByClassName("mapboxgl-canvas")] as HTMLCanvasElement[];
    useEffect(() => {
        // Skip first element as that is the default map layer
        for (const element of element1) {
            if (element?.style) element.style.filter = `brightness(${brightness}%)`;
        }
    }, [brightness, element1]);

    return <></>;
}

function setPathToCity(city: string) {
    // window.location.search = `?city=${encodeURIComponent(city)}`;
    window.history.pushState({}, "", encodeURIComponent(city));
}

export function App() {
    const path = window.location.pathname;

    let component: JSX.Element;
    if (path === "/bike") {
        component = <BikeMap />;
    } else if (GIF_RENDER) {
        component = <div>GIF Generator Mode</div>;
    } else {
        component = <RouteRangerApp />;
    }
    return <React.StrictMode>{component}</React.StrictMode>;
}

export function RouteRangerApp() {
    const queryClient = new QueryClient({});

    const path = decodeURIComponent(window.location.pathname).substring(1);

    let DEFAULT_CITY = "London";
    if (path in CITY_LOCATION) {
        DEFAULT_CITY = path;
    }

    const [currentCity, setCurrentCity] = useState(DEFAULT_CITY);
    const [currentStartingLoc, setCurrentStartingLoc] = useState(CITY_LOCATION[DEFAULT_CITY]);

    const [popupAccepted, setPopupAccepted] = useState(false);
    const [brightness, setBrightness] = useState(135);

    const setCityFromPill = (cityName: string) => {
        console.log("Set city", cityName)
        setCurrentCity(cityName);
        setCurrentStartingLoc(CITY_LOCATION[cityName]);
        setPathToCity(cityName);
    };

    const brightnessCtx = { brightness, setBrightness }
    return (
        <QueryClientProvider client={queryClient}>
            {popupAccepted ? null : <WelcomePopup acceptedPopupCallback={setPopupAccepted} />}
            <BlurBackground enabled={!popupAccepted}>
                <CityPillContainer
                    cities={["London"]}
                    setLocation={setCityFromPill}
                    currentCity={currentCity}
                />
                <BrightnessContext.Provider value={brightnessCtx}>
                    <MapboxGLCanvasBrightnessHack brightness={brightness} />
                    <ControlSidebar defaultStartLoc={currentStartingLoc} currentCity={currentCity} />
                </BrightnessContext.Provider>
                <InformationIcon
                    onClick={() => {
                        setPopupAccepted(false);
                    }}
                />
            </BlurBackground>
        </QueryClientProvider>
    );
}

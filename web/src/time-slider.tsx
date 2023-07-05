import { useEffect, useState } from 'preact/hooks'
import { formatDuration, formatTime } from "./format-details"
import { Header } from "./control-sidebar"
import track from "./analytics"

export function TimeSliderInner ({ duration, setDuration, text, min, max, formatFunc }) {
    const [iduration, setIduration] = useState(duration)

    const onChange = (element) => {
        const dur = parseInt(element.target.value)
        setIduration(dur)
    }

    const onMouseUp = (element) => {
        track("range-change", { text })
        const dur = parseInt(element.target.value)
        setDuration(dur)
    }

    return <div className="mt-2">
        <div>
            <label
                htmlFor="duration-range"
                className="float-left mb-1 text-sm font-medium text-gray-900"
            >
                {text}
            </label>
            <span
                id="duration-label"
                className="float-right inline-block mb-1 text-sm font-light text-gray-700"
            >{formatFunc(iduration)}</span>
        </div>
        <input
            id="duration-range"
            type="range"
            min={min}
            max={max}
            value={iduration}
            className="w-full h-1 bg-slate-300 rounded-lg appearance-none cursor-pointer"
            onChange={onChange}
            onMouseUp={onMouseUp}
        />
    </div>
}

export function TimeSlider ({ duration, setDuration, startTime, setStartTime }) {
    return (
        <div className="mt-2">
            <Header>Time Settings</Header>

            <TimeSliderInner duration={duration} setDuration={setDuration} formatFunc={formatDuration} min="1800" max="5400" text="Maximum duration of trip"/>
            <TimeSliderInner duration={startTime} setDuration={setStartTime} formatFunc={formatTime} min="18000" max="104400" text="Starting time"/>
        </div>
    )
}

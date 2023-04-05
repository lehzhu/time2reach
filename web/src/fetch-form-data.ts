const AGENCY_IDS = [
    "ttc",
    "up",
    "go",
    "yrt",
    "brampton",
    "miway",
    "grt"
];
export default function fetch_form_data() {
    const agencies = [];
    for (const id of AGENCY_IDS) {
        if ((<HTMLInputElement>document.getElementById(id)).checked) {
            agencies.push(id.toUpperCase());
        }
    }
    return agencies
}

export function fetch_modes_data() {
    const modes = [];
    for (const mode of ['bus', 'rail', 'tram', 'subway']) {
        if ((<HTMLInputElement>document.getElementById(mode)).checked) {
            modes.push(mode);
        }
    }
    return modes;
}
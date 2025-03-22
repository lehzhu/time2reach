// eslint-disable-next-line @typescript-eslint/naming-convention
// This is a stub since the original analytics service is no longer available
declare function sa_event(eventName: string, metadata?: Record<string, any>);

export default function track(name: string, properties: Record<string, any>) {
    try {
        console.log(`Analytics event: ${name}`, properties);
        // The original code below is commented out since the service is no longer available
        // if (window.sa_event) {
        //     sa_event(name, properties);
        // }
    } catch (e) {
        console.error("Error sending analytics", e);
    }
}

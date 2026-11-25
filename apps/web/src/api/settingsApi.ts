import type { InvestigationSettings, InvestigationSettingsOut } from "../types/settings";
import { request } from "./client";

// Investigation settings endpoints (BD31).
function settingsPath(investigationId: number): string {
    return `/investigations/${investigationId}/settings`;
}

// The effective values: the defaults if nothing was saved yet.
export function getSettings(investigationId: number): Promise<InvestigationSettingsOut> {
    return request(settingsPath(investigationId));
}

// A full replacement. 422 "indistinct_styles" if two types look the same (BD29).
export function saveSettings(investigationId: number, settings: InvestigationSettings): Promise<InvestigationSettingsOut> {
    return request(settingsPath(investigationId), { method: "PUT", body: JSON.stringify(settings) });
}

// Reset to defaults. Returns the defaults, so no second call is needed.
export function resetSettings(investigationId: number): Promise<InvestigationSettingsOut> {
    return request(settingsPath(investigationId), { method: "DELETE" });
}

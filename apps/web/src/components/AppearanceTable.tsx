import { DOCUMENT_TYPES, DOCUMENT_TYPE_LABELS, type DocumentType } from "../types/document";
import {
    EDGE_COLOR_OPTIONS,
    NODE_COLOR_OPTIONS,
    SHAPE_OPTIONS,
    type EdgeColorToken,
    type InvestigationSettings,
    type NodeColorToken,
    type NodeShape,
    type TypeStyle,
} from "../types/settings";
import { EdgePreview, NodePreview, Swatch } from "./StylePreview";

// Groups of document types that share a color and shape (D27: not allowed). Only groups of
// two or more are returned. The backend runs the same check (BD29).
export function findClashes(settings: InvestigationSettings): DocumentType[][] {
    const byStyle = new Map<string, DocumentType[]>();
    for (const type of DOCUMENT_TYPES) {
        const { color, shape } = settings.node_styles[type];
        const key = `${color}/${shape}`;
        byStyle.set(key, [...(byStyle.get(key) ?? []), type]);
    }
    return [...byStyle.values()].filter((group) => group.length > 1);
}

// "Error: Transaction and Misc look the same. ..." (UI-22). Three or more are joined with commas.
export function clashMessage(group: DocumentType[]): string {
    const names = group.map((type) => DOCUMENT_TYPE_LABELS[type]);
    const joined = names.length === 2 ? names.join(" and ") : `${names.slice(0, -1).join(", ")} and ${names.at(-1)}`;
    return `Error: ${joined} look the same. Change the color or shape of one.`;
}

interface AppearanceTableProps {
    value: InvestigationSettings;
    onChange: (next: InvestigationSettings) => void;
    clashes: DocumentType[][];
}

// One row per document type plus "Important connections" (settings-page "Layout").
// The Save and Reset buttons live on SettingsPage, which owns the requests.
export default function AppearanceTable({ value, onChange, clashes }: AppearanceTableProps) {
    function setStyle(type: DocumentType, change: Partial<TypeStyle>) {
        onChange({ ...value, node_styles: { ...value.node_styles, [type]: { ...value.node_styles[type], ...change } } });
    }

    return (
        <table className="appearance-table">
            <thead>
                <tr>
                    <th scope="col">Type</th>
                    <th scope="col">Preview</th>
                    <th scope="col">Color</th>
                    <th scope="col">Shape</th>
                </tr>
            </thead>
            <tbody>
                {DOCUMENT_TYPES.map((type) => {
                    const style = value.node_styles[type];
                    const clash = clashes.find((group) => group.includes(type));
                    const inputClass = clash ? "form-field__input form-field__input--error" : "form-field__input";
                    const label = DOCUMENT_TYPE_LABELS[type];
                    return (
                        <tr key={type}>
                            <th scope="row">
                                {label}
                                {clash && <p className="form-field__error">{clashMessage(clash)}</p>}
                            </th>
                            <td>
                                <NodePreview color={style.color} shape={style.shape} />
                            </td>
                            <td>
                                <span className="appearance-table__color">
                                    <Swatch color={style.color} />
                                    <select
                                        className={inputClass}
                                        aria-label={`${label} color`}
                                        aria-invalid={clash ? true : undefined}
                                        value={style.color}
                                        onChange={(event) => setStyle(type, { color: event.target.value as NodeColorToken })}
                                    >
                                        {NODE_COLOR_OPTIONS.map((option) => (
                                            <option key={option.value} value={option.value}>
                                                {option.label}
                                            </option>
                                        ))}
                                    </select>
                                </span>
                            </td>
                            <td>
                                <select
                                    className={inputClass}
                                    aria-label={`${label} shape`}
                                    aria-invalid={clash ? true : undefined}
                                    value={style.shape}
                                    onChange={(event) => setStyle(type, { shape: event.target.value as NodeShape })}
                                >
                                    {SHAPE_OPTIONS.map((option) => (
                                        <option key={option.value} value={option.value}>
                                            {option.label}
                                        </option>
                                    ))}
                                </select>
                            </td>
                        </tr>
                    );
                })}
                <tr>
                    <th scope="row">Important connections</th>
                    <td>
                        <EdgePreview color={value.important_edge_color} />
                    </td>
                    <td>
                        <span className="appearance-table__color">
                            <Swatch color={value.important_edge_color} />
                            <select
                                className="form-field__input"
                                aria-label="Important connections color"
                                value={value.important_edge_color}
                                onChange={(event) =>
                                    onChange({ ...value, important_edge_color: event.target.value as EdgeColorToken })
                                }
                            >
                                {EDGE_COLOR_OPTIONS.map((option) => (
                                    <option key={option.value} value={option.value}>
                                        {option.label}
                                    </option>
                                ))}
                            </select>
                        </span>
                    </td>
                    <td />
                </tr>
            </tbody>
        </table>
    );
}

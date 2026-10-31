import type { Certificate, SurveyOut } from "@/lib/types";
import { DASH, POSITIONS, POSITION_LABEL, fx, grouped, isNum, signed } from "@/lib/format";

const M_KEYS = new Set(["d_fp", "d_ap", "d_ms", "d_mm", "trim", "T_m"]);

function traceValue(k: string, v: number | null | undefined, barge: boolean): string {
  if (!isNum(v)) return DASH;
  if (M_KEYS.has(k)) return `${fx(v, barge ? 5 : 4)} m`;
  if (k.startsWith("corr_")) return `${signed(v, 2)} t`;
  if (k === "area_m2") return `${fx(v, 5)} m²`;
  if (k === "rho") return `${fx(v, 1)} kg/m³`;
  return `${grouped(v, 2)} t`;
}

/** Survey output: draft sheet with sources and t/mm, the program's intermediates, and the
 *  displacement / deductions / net / cargo lines shown separately (the server strips them on REFUSE). */
export function SurveyResult({ survey, booklet }: { survey: SurveyOut; booklet?: Certificate["booklet"] }) {
  const barge = !!survey.barge;
  const unit = barge ? "kg" : "t";
  const trace = Object.entries(survey.trace ?? {});
  return (
    <div className="survey-out">
      {!barge && survey.drafts ? (
        <div className="table-scroll">
          <table className="table">
            <caption className="table__caption">Draft sheet</caption>
            <thead>
              <tr>
                <th scope="col">Position</th>
                <th scope="col">Draft m</th>
                <th scope="col">Source</th>
                <th scope="col">Weight</th>
                <th scope="col">t per mm</th>
              </tr>
            </thead>
            <tbody>
              {POSITIONS.map((p) => (
                <tr key={p}>
                  <th scope="row">{POSITION_LABEL[p]}</th>
                  <td className="data num">{fx(survey.drafts?.[p], 4)}</td>
                  <td className={survey.sources?.[p] === "live" ? "src src--live" : "src"}>{survey.sources?.[p] ?? DASH}</td>
                  <td className="data num">{fx(survey.weights?.[p], 4)}</td>
                  <td className="data num">{fx(survey.t_per_mm?.[p], 3)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}

      {trace.length ? (
        <div className="table-scroll">
          <table className="table">
            <caption className="table__caption">Intermediates (printed by code)</caption>
            <tbody>
              {trace.map(([k, v]) => (
                <tr key={k}>
                  <th scope="row" className="data">
                    {k}
                  </th>
                  <td className="data num">{traceValue(k, v, barge)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}

      {survey.error ? <p className="error-inline data">{survey.error}</p> : null}
      {survey.gate_fail && survey.gate_fail.length ? (
        <ul className="error-inline small">
          {survey.gate_fail.map((g) => (
            <li key={g}>{g}</li>
          ))}
        </ul>
      ) : null}

      <dl className="lines">
        {isNum(survey.disp) ? (
          <div>
            <dt>Displacement</dt>
            <dd className="data">
              {grouped(survey.disp, barge ? 4 : 1)} {unit}
              {isNum(survey.u_disp) && survey.u_disp > 0 ? ` ± ${grouped(survey.u_disp, barge ? 4 : 1)}` : ""}
            </dd>
          </div>
        ) : null}
        {barge && isNum(survey.light) ? (
          <div>
            <dt>Light weight</dt>
            <dd className="data">
              {grouped(survey.light, 4)} {unit}
            </dd>
          </div>
        ) : null}
        {isNum(survey.deductions) ? (
          <div>
            <dt>Deductions</dt>
            <dd className="data">
              {grouped(survey.deductions, 1)} {unit}
              {survey.deductibles && Object.keys(survey.deductibles).length
                ? ` (${Object.entries(survey.deductibles)
                    .map(([k, v]) => `${k} ${grouped(v, 1)}`)
                    .join(" · ")})`
                : ""}
            </dd>
          </div>
        ) : null}
        {isNum(survey.net) ? (
          <div>
            <dt>Net</dt>
            <dd className="data">
              {grouped(survey.net, 1)} {unit}
            </dd>
          </div>
        ) : null}
        {"cargo" in survey ? (
          <div className="lines__cargo">
            <dt>Cargo{survey.cargo_kind ? ` (${survey.cargo_kind})` : ""}</dt>
            <dd className="data">
              {isNum(survey.cargo)
                ? `${grouped(survey.cargo, barge ? 4 : 1)} ${unit}${isNum(survey.u_cargo) ? ` ± ${grouped(survey.u_cargo, barge ? 4 : 1)}` : ""}`
                : barge
                  ? DASH
                  : "not computed — needs a lightship constant or an initial net"}
            </dd>
          </div>
        ) : null}
      </dl>
      {survey.u_label ? <p className="muted small">u covers: {survey.u_label}</p> : null}

      {booklet && isNum(booklet.printed_disp_t) ? (
        <p className="small">
          Booklet condition <span className="data">{booklet.condition}</span> (p. <span className="data">{booklet.page}</span>)
          prints <span className="data">{grouped(booklet.printed_disp_t, 1)} t</span>; the program printed{" "}
          <span className="data">{grouped(survey.disp, 1)} t</span>
          {isNum(survey.disp)
            ? ` (${fx(((survey.disp - booklet.printed_disp_t) / booklet.printed_disp_t) * 100, 3)} %)`
            : ""}
          .
        </p>
      ) : null}

      {survey.consequence && isNum(survey.consequence.tpc_t_per_cm) ? (
        <p className="consequence">
          Ro-Ro test ship: 1 cm at this draft = <span className="data">{fx(survey.consequence.tpc_t_per_cm, 2)} t</span>{" "}
          (illustrative, not a bulk carrier)
        </p>
      ) : null}
      {survey.consequence && isNum(survey.consequence.g_per_mm) ? (
        <p className="consequence">
          Barge: 1 mm of draft = <span className="data">{fx(survey.consequence.g_per_mm, 2)} g</span> of cargo
        </p>
      ) : null}
    </div>
  );
}

import type { SelftestRow, SelftestSummary } from "@/lib/types";
import { fx, grouped, tiny } from "@/lib/format";

export function SelfTestVerdict({ st }: { st: SelftestSummary }) {
  const probes = st.probes_raised ?? [];
  return (
    <p className={`verdict ${st.verdict === "PASS" ? "verdict--pass" : "verdict--fail"}`}>
      <span className="verdict__word">{st.verdict}</span>
      <span className="data">
        {st.pass_count}/{st.n} printed conditions
      </span>
      <span className="data">
        out-of-table probes refused {probes.filter(Boolean).length}/{probes.length}
      </span>
      <span className="data">
        vs our reference program, {st.differential_n ?? "—"} cases · max difference {tiny(st.differential_max_err_pct)} %
        {st.differential_failures != null ? ` · ${st.differential_failures} failures` : ""}
      </span>
    </p>
  );
}

/** The booklet's printed conditions vs the program's output, row by row. */
export function SelfTestTable({ rows }: { rows: SelftestRow[] }) {
  return (
    <div className="table-scroll">
      <table className="table table--selftest">
        <caption className="sr-only">Self-test: booklet printed displacement against the program output</caption>
        <thead>
          <tr>
            <th scope="col">Condition</th>
            <th scope="col">Page</th>
            <th scope="col">Printed t</th>
            <th scope="col">Program t</th>
            <th scope="col">Error %</th>
            <th scope="col">Result</th>
            <th scope="col">First diverging</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r.cond_id} className={r.passed ? "" : "row--fail"}>
              <th scope="row" className="data">
                {r.cond_id}
              </th>
              <td className="data">{r.page}</td>
              <td className="data num">{grouped(r.expected)}</td>
              <td className="data num">{grouped(r.got)}</td>
              <td className="data num">{fx(r.err_pct, 4)}</td>
              <td className={r.passed ? "pass" : "fail"}>{r.passed ? "PASS" : "FAIL"}</td>
              <td className="data">{r.first_diverging ?? (r.error ? r.error.slice(0, 60) : "—")}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

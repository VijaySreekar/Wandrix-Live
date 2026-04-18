import { SectionCard } from "@/components/ui/section-card";
import type { TravelPackageResponse } from "@/types/package";


type PackageResultProps = {
  result: TravelPackageResponse | null;
};


export function PackageResult({ result }: PackageResultProps) {
  if (!result) {
    return (
      <SectionCard
        eyebrow="Live output"
        title="Generated package will appear here"
        className="h-full"
      >
        <p className="text-sm leading-7 text-foreground/70">
          Submit the trip brief on the left to see the generated summary,
          inclusions, recommendations, and day-by-day itinerary.
        </p>
      </SectionCard>
    );
  }

  return (
    <SectionCard eyebrow="Live output" title={result.title} className="h-full">
      <div className="space-y-6">
        <div className="rounded-[1.5rem] bg-[#20150d] p-5 text-[#fff4e8]">
          <p className="text-sm leading-7 text-[#f7ddc8]">{result.summary}</p>
          <div className="mt-4 grid gap-3 text-sm sm:grid-cols-3">
            <div>
              <p className="text-[#f4b383]">Route</p>
              <p className="font-medium">
                {result.origin} to {result.destination}
              </p>
            </div>
            <div>
              <p className="text-[#f4b383]">Nights</p>
              <p className="font-medium">{result.duration_nights}</p>
            </div>
            <div>
              <p className="text-[#f4b383]">Estimated total</p>
              <p className="font-medium">
                {result.estimated_total_gbp
                  ? `GBP ${result.estimated_total_gbp.toLocaleString()}`
                  : "TBC"}
              </p>
            </div>
          </div>
        </div>

        <div className="grid gap-4 lg:grid-cols-2">
          <div className="rounded-[1.5rem] border border-panel-border bg-white/80 p-5 dark:bg-black/10">
            <h3 className="text-lg font-semibold">Inclusions</h3>
            <ul className="mt-3 grid gap-2 text-sm leading-6 text-foreground/75">
              {result.inclusions.map((item) => (
                <li key={item} className="rounded-xl bg-black/5 px-3 py-2 dark:bg-white/5">
                  {item}
                </li>
              ))}
            </ul>
          </div>

          <div className="rounded-[1.5rem] border border-panel-border bg-white/80 p-5 dark:bg-black/10">
            <h3 className="text-lg font-semibold">Recommendations</h3>
            <ul className="mt-3 grid gap-2 text-sm leading-6 text-foreground/75">
              {result.recommendations.map((item) => (
                <li key={item} className="rounded-xl bg-black/5 px-3 py-2 dark:bg-white/5">
                  {item}
                </li>
              ))}
            </ul>
          </div>
        </div>

        <div className="space-y-3">
          <h3 className="text-lg font-semibold">Itinerary</h3>
          <div className="grid gap-3">
            {result.itinerary.map((day) => (
              <article
                key={`${day.day}-${day.date}`}
                className="rounded-[1.5rem] border border-panel-border bg-white/80 p-5 dark:bg-black/10"
              >
                <div className="mb-3 flex items-center justify-between gap-4">
                  <h4 className="font-semibold">
                    Day {day.day}
                  </h4>
                  <p className="text-sm text-foreground/60">{day.date}</p>
                </div>
                <div className="grid gap-3 text-sm leading-6 text-foreground/75">
                  <p><span className="font-semibold text-foreground">Morning:</span> {day.morning}</p>
                  <p><span className="font-semibold text-foreground">Afternoon:</span> {day.afternoon}</p>
                  <p><span className="font-semibold text-foreground">Evening:</span> {day.evening}</p>
                </div>
              </article>
            ))}
          </div>
        </div>
      </div>
    </SectionCard>
  );
}

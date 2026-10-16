import Dashboard from "@/components/Dashboard";

export default function Page() {
  return (
    <>
      <section className="mb-8">
        <h1 className="text-2xl font-semibold">Agents</h1>
        <p className="text-slate-400 mt-1">
          Run a working agent against live data. Results are scraped + analyzed by Claude in real time.
        </p>
      </section>
      <Dashboard />
    </>
  );
}

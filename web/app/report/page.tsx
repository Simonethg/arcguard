"use client";

import { ReportView } from "@/components/ReportView";
import { EXAMPLE_REPORT } from "@/lib/sample-report";

export default function ReportPage() {
  return (
    <div data-testid="report-page">
      <ReportView report={EXAMPLE_REPORT} banner="static" headingLevel="h1" />
    </div>
  );
}

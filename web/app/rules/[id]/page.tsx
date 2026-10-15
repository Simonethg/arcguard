import { notFound } from "next/navigation";
import { RULES, isRuleId } from "@/content/rules";
import { RuleScreen } from "@/components/RuleScreen";

export function generateStaticParams() {
  return RULES.map((rule) => ({ id: rule.id }));
}

export const dynamicParams = false;

export default async function RulePage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  if (!isRuleId(id)) notFound();
  return <RuleScreen id={id} />;
}

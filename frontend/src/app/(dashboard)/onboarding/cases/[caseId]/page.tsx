import { OnboardingDetail } from '@/components/onboarding/OnboardingDetail';

export default function OnboardingCaseDetailPage({ params }: { params: { caseId: string } }) {
  return <OnboardingDetail processId={params.caseId} />;
}

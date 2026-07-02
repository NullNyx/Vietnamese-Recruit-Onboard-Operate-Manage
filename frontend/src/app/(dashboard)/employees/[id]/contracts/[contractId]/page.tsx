"use client";

import { useEffect } from "react";
import { useParams, useRouter } from "next/navigation";

export default function EmployeeContractDetailRedirect() {
  const params = useParams();
  const router = useRouter();
  const employeeId = params.id as string;
  const contractId = params.contractId as string;

  useEffect(() => {
    router.replace(`/contracts/${contractId}?employee=${employeeId}`);
  }, [contractId, employeeId, router]);

  return null;
}

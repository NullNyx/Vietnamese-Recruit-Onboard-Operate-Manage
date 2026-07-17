import { redirect } from 'next/navigation';

/** /employee/dashboard mirrors the ESS home; keep a single entrypoint at /employee. */
export default function EmployeeDashboardRedirect() {
  redirect('/employee');
}
import AppLayout from "@/components/layout/AppLayout";

import {
  AppRoutes,
} from "@/routes";

export default function App() {
  return (
    <AppLayout>
      <AppRoutes />
    </AppLayout>
  );
}
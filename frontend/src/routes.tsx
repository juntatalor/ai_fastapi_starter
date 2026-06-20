import { createBrowserRouter } from "react-router-dom";

import { AppLayout } from "./components/AppLayout";
import { ProtectedRoute } from "./components/ProtectedRoute";
import { HelloPage } from "./pages/HelloPage";
import { LoginPage } from "./pages/LoginPage";
import { ProfilePage } from "./pages/ProfilePage";
import { YandexCallbackPage } from "./pages/YandexCallbackPage";
import { UsersPage } from "./pages/admin/UsersPage";

export const router = createBrowserRouter([
  { path: "/login", element: <LoginPage /> },
  { path: "/oauth/yandex", element: <YandexCallbackPage /> },
  {
    path: "/",
    element: (
      <ProtectedRoute>
        <AppLayout />
      </ProtectedRoute>
    ),
    children: [
      { index: true, element: <HelloPage /> },
      { path: "profile", element: <ProfilePage /> },
      {
        path: "admin/users",
        element: (
          <ProtectedRoute role="admin">
            <UsersPage />
          </ProtectedRoute>
        ),
      },
    ],
  },
]);

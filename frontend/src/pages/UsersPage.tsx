import { Navigate } from "react-router-dom";
import { useAuth } from "../AuthContext";
import { UserManagement } from "../components/UserManagement";

export function UsersPage() {
  const { user } = useAuth();
  if (user?.role !== "admin") {
    return <Navigate to="/" replace />;
  }
  return <UserManagement />;
}

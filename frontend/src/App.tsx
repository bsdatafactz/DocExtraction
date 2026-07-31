import { Navigate, Route, BrowserRouter, Routes, useLocation } from "react-router-dom";
import { AuthProvider, useAuth } from "./AuthContext";
import { TopNav } from "./components/TopNav";
import { DocumentDetailPage } from "./pages/DocumentDetailPage";
import { FormTypesPage } from "./pages/FormTypesPage";
import { LoginPage } from "./pages/LoginPage";
import { OverviewPage } from "./pages/OverviewPage";
import { ProjectsPage } from "./pages/ProjectsPage";
import { SignupPage } from "./pages/SignupPage";
import { UploadPage } from "./pages/UploadPage";
import { UsageCostPage } from "./pages/UsageCostPage";
import { UsersPage } from "./pages/UsersPage";
import "./App.css";

function ProtectedLayout({ children }: { children: React.ReactNode }) {
  const { user } = useAuth();
  const location = useLocation();

  if (!user) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  const wide = location.pathname.includes("/documents/");

  return (
    <div className={`app ${wide ? "app--wide" : ""}`}>
      <TopNav />
      <div className="app-content">{children}</div>
    </div>
  );
}

function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/signup" element={<SignupPage />} />
      <Route
        path="/"
        element={
          <ProtectedLayout>
            <OverviewPage />
          </ProtectedLayout>
        }
      />
      <Route
        path="/projects"
        element={
          <ProtectedLayout>
            <ProjectsPage />
          </ProtectedLayout>
        }
      />
      <Route
        path="/users"
        element={
          <ProtectedLayout>
            <UsersPage />
          </ProtectedLayout>
        }
      />
      <Route
        path="/types"
        element={
          <ProtectedLayout>
            <FormTypesPage />
          </ProtectedLayout>
        }
      />
      <Route
        path="/cost"
        element={
          <ProtectedLayout>
            <UsageCostPage />
          </ProtectedLayout>
        }
      />
      <Route path="/projects/:projectId" element={<Navigate to="upload" replace />} />
      <Route
        path="/projects/:projectId/upload"
        element={
          <ProtectedLayout>
            <UploadPage />
          </ProtectedLayout>
        }
      />
      <Route
        path="/projects/:projectId/documents/:documentId"
        element={
          <ProtectedLayout>
            <DocumentDetailPage />
          </ProtectedLayout>
        }
      />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <AppRoutes />
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;

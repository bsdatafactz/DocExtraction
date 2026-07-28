import { Navigate, Route, BrowserRouter, Routes, useLocation } from "react-router-dom";
import { AuthProvider, useAuth } from "./AuthContext";
import { TopNav } from "./components/TopNav";
import { DocumentDetailPage } from "./pages/DocumentDetailPage";
import { HomePage } from "./pages/HomePage";
import { LoginPage } from "./pages/LoginPage";
import { ReviewQueuePage } from "./pages/ReviewQueuePage";
import { SignupPage } from "./pages/SignupPage";
import { UploadPage } from "./pages/UploadPage";
import "./App.css";

function ProtectedLayout({ children }: { children: React.ReactNode }) {
  const { user } = useAuth();
  const location = useLocation();

  if (!user) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  const wide = location.pathname.startsWith("/documents/");

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
            <HomePage />
          </ProtectedLayout>
        }
      />
      <Route
        path="/projects/:projectId/upload"
        element={
          <ProtectedLayout>
            <UploadPage />
          </ProtectedLayout>
        }
      />
      <Route
        path="/projects/:projectId/review"
        element={
          <ProtectedLayout>
            <ReviewQueuePage />
          </ProtectedLayout>
        }
      />
      <Route
        path="/documents/:documentId"
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

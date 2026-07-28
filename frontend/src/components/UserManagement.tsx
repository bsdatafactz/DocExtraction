import { useCallback, useEffect, useState } from "react";
import { deleteUser, listUsers, updateUserRole, type UserSummary } from "../api";
import { useAuth } from "../AuthContext";
import { ConfirmDialog } from "./ConfirmDialog";

function errorMessage(err: unknown): string {
  return err instanceof Error ? err.message : "Something went wrong.";
}

export function UserManagement() {
  const { user: currentUser } = useAuth();
  const [users, setUsers] = useState<UserSummary[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [updatingId, setUpdatingId] = useState<number | null>(null);
  const [pendingDelete, setPendingDelete] = useState<UserSummary | null>(null);

  const refresh = useCallback(async () => {
    try {
      setUsers(await listUsers());
    } catch (err) {
      setError(errorMessage(err));
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  async function handleToggleRole(u: UserSummary) {
    const nextRole = u.role === "admin" ? "user" : "admin";
    setUpdatingId(u.id);
    try {
      await updateUserRole(u.id, nextRole);
      await refresh();
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setUpdatingId(null);
    }
  }

  async function confirmDelete() {
    if (!pendingDelete) return;
    setUpdatingId(pendingDelete.id);
    try {
      await deleteUser(pendingDelete.id);
      await refresh();
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setUpdatingId(null);
      setPendingDelete(null);
    }
  }

  return (
    <div>
      <p className="page-subtitle">
        Admin-only. Anyone signing up starts as a User — promote someone here to give them
        delete/approve access.
      </p>
      {error && (
        <div className="error-banner">
          <span>{error}</span>
          <button onClick={() => setError(null)}>Dismiss</button>
        </div>
      )}
      <table className="queue-table">
        <thead>
          <tr>
            <th>Email</th>
            <th>Role</th>
            <th>Joined</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {users.map((u) => (
            <tr key={u.id}>
              <td>{u.email}</td>
              <td>
                <span className={`badge ${u.role === "admin" ? "badge-approved" : "badge-queued"}`}>
                  {u.role === "admin" ? "Admin" : "User"}
                </span>
              </td>
              <td>{new Date(u.created_at).toLocaleDateString()}</td>
              <td className="queue-actions">
                {u.id === currentUser?.id ? (
                  <span className="page-subtitle">You</span>
                ) : (
                  <>
                    <button disabled={updatingId === u.id} onClick={() => handleToggleRole(u)}>
                      {updatingId === u.id
                        ? "Updating…"
                        : u.role === "admin"
                          ? "Demote to User"
                          : "Promote to Admin"}
                    </button>
                    <button
                      className="btn-danger"
                      disabled={updatingId === u.id}
                      onClick={() => setPendingDelete(u)}
                    >
                      Delete
                    </button>
                  </>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {pendingDelete && (
        <ConfirmDialog
          message={`Delete user "${pendingDelete.email}"? This can't be undone.`}
          onConfirm={confirmDelete}
          onCancel={() => setPendingDelete(null)}
        />
      )}
    </div>
  );
}

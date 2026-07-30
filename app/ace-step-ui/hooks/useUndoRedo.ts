import { useCallback, useRef } from 'react';
import { projectsApi } from '../services/api';

interface UndoRedoState {
  canUndo: boolean;
  canRedo: boolean;
  undoAction: string | null;
  redoAction: string | null;
}

interface UseUndoRedoOptions {
  projectId: string | null;
  token: string | null;
  onUndo: (params: Record<string, any>) => void;
  onRedo: (params: Record<string, any>) => void;
}

export function useUndoRedo({ projectId, token, onUndo, onRedo }: UseUndoRedoOptions) {
  const redoStackRef = useRef<{ params: Record<string, any>; action: string }[]>([]);
  const stateRef = useRef<UndoRedoState>({
    canUndo: false,
    canRedo: false,
    undoAction: null,
    redoAction: null,
  });

  const refreshState = useCallback(async () => {
    if (!projectId || !token) {
      stateRef.current = { canUndo: false, canRedo: false, undoAction: null, redoAction: null };
      return stateRef.current;
    }
    try {
      const result = await projectsApi.getChangelogs(projectId, token, { limit: 1, offset: 0 });
      const canUndo = result.total > 0;
      const undoAction = result.changelogs.length > 0 ? result.changelogs[0].action : null;
      stateRef.current = {
        canUndo,
        canRedo: redoStackRef.current.length > 0,
        undoAction,
        redoAction: redoStackRef.current.length > 0 ? redoStackRef.current[redoStackRef.current.length - 1].action : null,
      };
    } catch {
      stateRef.current = { canUndo: false, canRedo: redoStackRef.current.length > 0, undoAction: null, redoAction: null };
    }
    return stateRef.current;
  }, [projectId, token]);

  const undo = useCallback(async () => {
    if (!projectId || !token || !stateRef.current.canUndo) return null;
    try {
      const result = await projectsApi.undoProject(projectId, token);
      redoStackRef.current.push({
        params: result.project.params,
        action: result.undone_action,
      });
      onUndo(result.project.params);
      await refreshState();
      return result;
    } catch (error) {
      console.error('Undo failed:', error);
      return null;
    }
  }, [projectId, token, onUndo, refreshState]);

  const redo = useCallback(async () => {
    if (!projectId || !token || redoStackRef.current.length === 0) return null;
    const redoItem = redoStackRef.current.pop()!;
    try {
      await projectsApi.updateProject(projectId, {
        params: redoItem.params,
        changelog_label: 'redo',
      }, token);
      onRedo(redoItem.params);
      await refreshState();
      return redoItem;
    } catch (error) {
      console.error('Redo failed:', error);
      redoStackRef.current.push(redoItem);
      return null;
    }
  }, [projectId, token, onRedo, refreshState]);

  const clearRedoStack = useCallback(() => {
    redoStackRef.current = [];
    stateRef.current.canRedo = false;
    stateRef.current.redoAction = null;
  }, []);

  return {
    undo,
    redo,
    refreshState,
    clearRedoStack,
    getState: () => stateRef.current,
  };
}

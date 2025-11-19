/**
 * Hierarchical Navigation Tree Component
 * Displays navigation as a collapsible tree with sorting and editing capabilities.
 */
import React, { useState, useCallback } from 'react';
import { 
  ChevronRight, 
  ChevronDown, 
  Edit3, 
  Plus, 
  Trash2, 
  Save, 
  X, 
  ExternalLink,
  GripVertical
} from 'lucide-react';
import { NavNode } from '../lib/types.confirm';
import { confirmationUtils } from '../lib/api.confirm';

interface NavigationTreeProps {
  nodes: NavNode[];
  onUpdate: (nodes: NavNode[]) => void;
  saving?: boolean;
}

type SortMode = 'original' | 'az';
type EditMode = 'view' | 'edit';

interface EditingState {
  mode: EditMode;
  editingNode: string | null;
  expandedNodes: Set<string>;
  sortMode: SortMode;
}

export default function NavigationTree({ nodes, onUpdate, saving = false }: NavigationTreeProps) {
  const [state, setState] = useState<EditingState>({
    mode: 'view',
    editingNode: null,
    expandedNodes: new Set(),
    sortMode: 'original'
  });

  const toggleExpanded = useCallback((nodeId: string) => {
    setState(prev => ({
      ...prev,
      expandedNodes: prev.expandedNodes.has(nodeId) 
        ? new Set([...prev.expandedNodes].filter(id => id !== nodeId))
        : new Set([...prev.expandedNodes, nodeId])
    }));
  }, []);

  const toggleSortMode = useCallback(() => {
    setState(prev => ({
      ...prev,
      sortMode: prev.sortMode === 'original' ? 'az' : 'original'
    }));
  }, []);

  const toggleEditMode = useCallback(() => {
    setState(prev => ({
      ...prev,
      mode: prev.mode === 'view' ? 'edit' : 'view',
      editingNode: null
    }));
  }, []);

  const startEditing = useCallback((nodeId: string) => {
    setState(prev => ({
      ...prev,
      editingNode: nodeId
    }));
  }, []);

  const cancelEditing = useCallback(() => {
    setState(prev => ({
      ...prev,
      editingNode: null
    }));
  }, []);

  const updateNode = useCallback((path: number[], field: 'label' | 'href', value: string) => {
    const updatedNodes = [...nodes];
    let current = updatedNodes;
    
    // Navigate to the parent of the target node
    for (let i = 0; i < path.length - 1; i++) {
      current = current[path[i]].children || [];
    }
    
    const nodeIndex = path[path.length - 1];
    current[nodeIndex] = {
      ...current[nodeIndex],
      [field]: value,
      id: field === 'label' || field === 'href' 
        ? confirmationUtils.generateNodeId(
            field === 'label' ? value : current[nodeIndex].label,
            field === 'href' ? value : current[nodeIndex].href
          )
        : current[nodeIndex].id
    };
    
    onUpdate(updatedNodes);
  }, [nodes, onUpdate]);

  const addChild = useCallback((path: number[]) => {
    const updatedNodes = [...nodes];
    let current = updatedNodes;
    
    // Navigate to the target node
    for (let i = 0; i < path.length - 1; i++) {
      current = current[path[i]].children || [];
    }
    
    const nodeIndex = path[path.length - 1];
    const parentNode = current[nodeIndex];
    
    if (!parentNode.children) {
      parentNode.children = [];
    }
    
    const newChild: NavNode = {
      id: confirmationUtils.generateNodeId('New Item', '#'),
      label: 'New Item',
      href: '#',
      order: parentNode.children.length
    };
    
    parentNode.children.push(newChild);
    onUpdate(updatedNodes);
    
    // Start editing the new child
    setState(prev => ({
      ...prev,
      editingNode: newChild.id
    }));
  }, [nodes, onUpdate]);

  const removeNode = useCallback((path: number[]) => {
    if (path.length === 1) {
      // Remove top-level node
      const updatedNodes = nodes.filter((_, index) => index !== path[0]);
      onUpdate(updatedNodes);
    } else {
      // Remove child node
      const updatedNodes = [...nodes];
      let current = updatedNodes;
      
      for (let i = 0; i < path.length - 1; i++) {
        current = current[path[i]].children || [];
      }
      
      const nodeIndex = path[path.length - 1];
      current.splice(nodeIndex, 1);
      onUpdate(updatedNodes);
    }
  }, [nodes, onUpdate]);

  const saveChanges = useCallback(() => {
    setState(prev => ({
      ...prev,
      mode: 'view',
      editingNode: null
    }));
  }, []);

  // Apply sorting to nodes
  const sortedNodes = confirmationUtils.applySort(nodes, state.sortMode);

  const renderNode = (node: NavNode, path: number[], level: number = 0): React.ReactNode => {
    const hasChildren = node.children && node.children.length > 0;
    const isExpanded = state.expandedNodes.has(node.id);
    const isEditing = state.editingNode === node.id;
    const isEditMode = state.mode === 'edit';

    return (
      <div key={node.id} className={`ml-${level * 4}`}>
        <div className="flex items-center gap-2 py-2 px-3 hover:bg-gray-50 dark:hover:bg-gray-700 rounded">
          {/* Expand/Collapse Button */}
          {hasChildren ? (
            <button
              onClick={() => toggleExpanded(node.id)}
              className="p-1 hover:bg-gray-200 dark:hover:bg-gray-600 rounded"
            >
              {isExpanded ? (
                <ChevronDown className="w-4 h-4 text-gray-500 dark:text-gray-400" />
              ) : (
                <ChevronRight className="w-4 h-4 text-gray-500 dark:text-gray-400" />
              )}
            </button>
          ) : (
            <div className="w-6"></div>
          )}

          {/* Drag Handle (Edit Mode) */}
          {isEditMode && (
            <GripVertical className="w-4 h-4 text-gray-400 dark:text-gray-500 cursor-grab" />
          )}

          {/* Node Content */}
          <div className="flex-1 flex items-center gap-2">
            {isEditing ? (
              <>
                <input
                  type="text"
                  value={node.label}
                  onChange={(e) => updateNode(path, 'label', e.target.value)}
                  className="flex-1 px-2 py-1 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 rounded text-sm"
                  placeholder="Label"
                  autoFocus
                />
                <input
                  type="text"
                  value={node.href}
                  onChange={(e) => updateNode(path, 'href', e.target.value)}
                  className="flex-1 px-2 py-1 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 rounded text-sm"
                  placeholder="URL"
                />
                <button
                  onClick={cancelEditing}
                  className="p-1 text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300"
                >
                  <X className="w-4 h-4" />
                </button>
              </>
            ) : (
              <>
                <span className="text-sm font-medium text-gray-900 dark:text-gray-100">{node.label}</span>
                {node.href && (
                  <div className="flex items-center gap-1">
                    <span className="text-xs text-gray-500 dark:text-gray-400">({node.href})</span>
                    <ExternalLink className="w-3 h-3 text-gray-400 dark:text-gray-500" />
                  </div>
                )}
              </>
            )}
          </div>

          {/* Action Buttons (Edit Mode) */}
          {isEditMode && !isEditing && (
            <div className="flex items-center gap-1">
              <button
                onClick={() => startEditing(node.id)}
                className="p-1 text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300"
                title="Edit"
              >
                <Edit3 className="w-4 h-4" />
              </button>
              <button
                onClick={() => addChild(path)}
                className="p-1 text-green-600 dark:text-green-400 hover:text-green-800 dark:hover:text-green-300"
                title="Add child"
              >
                <Plus className="w-4 h-4" />
              </button>
              <button
                onClick={() => removeNode(path)}
                className="p-1 text-red-600 dark:text-red-400 hover:text-red-800 dark:hover:text-red-300"
                title="Remove"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
          )}
        </div>

        {/* Children */}
        {hasChildren && isExpanded && (
          <div className="space-y-1">
            {node.children!.map((child, index) => 
              renderNode(child, [...path, index], level + 1)
            )}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="space-y-4">
      {/* Controls */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          {/* Sort Toggle */}
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-600 dark:text-gray-400">Sort:</span>
            <button
              onClick={toggleSortMode}
              className={`px-3 py-1 text-sm rounded ${
                state.sortMode === 'original'
                  ? 'bg-blue-100 dark:bg-blue-900/50 text-blue-700 dark:text-blue-300'
                  : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-600'
              }`}
            >
              Original
            </button>
            <button
              onClick={toggleSortMode}
              className={`px-3 py-1 text-sm rounded ${
                state.sortMode === 'az'
                  ? 'bg-blue-100 dark:bg-blue-900/50 text-blue-700 dark:text-blue-300'
                  : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-600'
              }`}
            >
              A→Z
            </button>
          </div>
        </div>

        {/* Edit Mode Toggle */}
        <div className="flex items-center gap-2">
          {state.mode === 'edit' ? (
            <>
              <button
                onClick={saveChanges}
                disabled={saving}
                className="flex items-center gap-2 px-3 py-1 bg-green-600 dark:bg-green-700 text-white rounded text-sm hover:bg-green-700 dark:hover:bg-green-600 disabled:opacity-50"
              >
                <Save className="w-4 h-4" />
                {saving ? 'Saving...' : 'Save'}
              </button>
              <button
                onClick={toggleEditMode}
                className="px-3 py-1 text-sm text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200"
              >
                Cancel
              </button>
            </>
          ) : (
            <button
              onClick={toggleEditMode}
              className="flex items-center gap-2 px-3 py-1 bg-blue-600 dark:bg-blue-700 text-white rounded text-sm hover:bg-blue-700 dark:hover:bg-blue-600"
            >
              <Edit3 className="w-4 h-4" />
              Edit Navigation
            </button>
          )}
        </div>
      </div>

      {/* Tree */}
      <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4">
        {sortedNodes.length === 0 ? (
          <div className="text-center py-8 text-gray-500 dark:text-gray-400">
            <p className="text-sm">No navigation items found</p>
          </div>
        ) : (
          <div className="space-y-1">
            {sortedNodes.map((node, index) => 
              renderNode(node, [index])
            )}
          </div>
        )}
      </div>

      {/* Add Top-Level Item (Edit Mode) */}
      {state.mode === 'edit' && (
        <div className="text-center">
          <button
            onClick={() => {
              const newItem: NavNode = {
                id: confirmationUtils.generateNodeId('New Item', '#'),
                label: 'New Item',
                href: '#',
                order: nodes.length
              };
              onUpdate([...nodes, newItem]);
              setState(prev => ({
                ...prev,
                editingNode: newItem.id
              }));
            }}
            className="px-4 py-2 bg-green-600 dark:bg-green-700 text-white rounded text-sm hover:bg-green-700 dark:hover:bg-green-600"
          >
            <Plus className="w-4 h-4 inline mr-2" />
            Add Top-Level Item
          </button>
        </div>
      )}
    </div>
  );
}

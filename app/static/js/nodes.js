document.addEventListener('DOMContentLoaded', function() {
    const token = localStorage.getItem('auth_token');
    if (!token) {
        window.location.href = '/auth/login';
        return;
    }

    try {
        // Load initial data
        loadNodes();

        // Add event listeners
        document.getElementById('searchButton')?.addEventListener('click', loadNodes);
        document.getElementById('statusFilter')?.addEventListener('change', loadNodes);
        document.getElementById('saveNodeButton')?.addEventListener('click', saveNode);
        document.getElementById('logout-btn')?.addEventListener('click', logout);
        document.getElementById('saveEditNodeButton').addEventListener('click', saveEditedNode);
        document.getElementById('confirmDeleteNodeButton').addEventListener('click', function () {
            const nodeId = this.getAttribute('data-node-id');
            deleteNode(nodeId);
        });
        document.getElementById('saveAlertButton').addEventListener('click', saveAlert);
    } catch (error) {
        console.error('Error setting up event listeners:', error);
    }
});

async function loadNodes() {
    const token = localStorage.getItem('auth_token');
    const searchTerm = document.getElementById('searchInput')?.value || '';
    const statusFilter = document.getElementById('statusFilter')?.value || 'all';
    const tbody = document.getElementById('nodesTableBody');

    // Show loading state
    tbody.innerHTML = '<tr><td colspan="5" class="text-center">Đang tải dữ liệu...</td></tr>';

    try {
        const response = await fetch(`/api/nodes?search=${encodeURIComponent(searchTerm)}&status=${encodeURIComponent(statusFilter)}`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Accept': 'application/json'
            }
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const nodes = await response.json();
        if (!nodes || !Array.isArray(nodes)) {
            throw new Error('Invalid response format');
        }

        // Fetch metrics for each node
        const metricsPromises = nodes.map(async (node) => {
            try {
                const metricsResponse = await fetch(`/api/nodes/${node.id}/metrics`, {
                    method: 'GET',
                    headers: {
                        'Authorization': `Bearer ${token}`
                    }
                });

                if (!metricsResponse.ok) {
                    throw new Error('Failed to fetch metrics');
                }

                const metrics = await metricsResponse.json();
                return { ...node, metrics };
            } catch (error) {
                console.error(`Error fetching metrics for node ${node.id}:`, error);
                return { ...node, metrics: { nodeExporter: 'Null', promtail: 'Null' } };
            }
        });

        const nodesWithMetrics = await Promise.all(metricsPromises);
        updateNodesTable(nodesWithMetrics);
    } catch (error) {
        console.error('Error loading nodes:', error);
        tbody.innerHTML = `
            <tr>
                <td colspan="5" class="text-center">
                    <div class="alert alert-danger mb-0">
                        Không thể tải danh sách nodes. 
                        <button class="btn btn-link p-0 ms-2" onclick="loadNodes()">
                            Thử lại
                        </button>
                    </div>
                </td>
            </tr>
        `;
    }
}

function updateNodesTable(nodes) {
    const tbody = document.getElementById('nodesTableBody');
    if (!tbody) {
        console.error('Table body element not found');
        return;
    }

    try {
        if (!nodes || nodes.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" class="text-center">Không có nodes nào</td></tr>';
            return;
        }

        let nodesHtml = '';

        nodes.forEach((node, index) => {
            const statusClass = node.status === 'active' ? 'success' : 'danger';
            const statusText = node.status === 'active' ? 'Hoạt động' : 'Không hoạt động';
            const nodeExporter = node.metrics?.nodeExporter || 'NodeExporter Null';
            const promtail = node.metrics?.promtail || 'Promtail Null';

            nodesHtml += `
                <tr>
                    <td>${index + 1}</td>
                    <td>${node.name || ''}</td>
                    <td>${node.ipAddress || ''}</td>
                    <td><span class="badge bg-${statusClass}">${statusText}</span></td>
                    <td>
                        <span class="badge bg-warning text-dark">${nodeExporter}</span>
                        <span class="badge bg-primary">${promtail}</span>
                        <button class="btn btn-sm btn-link text-info" onclick="openCheckConfigModal(${node.id})">
                            <i class="bi bi-gear"></i>
                        </button>
                    </td>
                    <td class="text-center">
                        <button class="btn btn-sm btn-link text-success" onclick="openAddAlertModal('${node.id}')">
                            <i class="bi bi-plus-circle"></i>
                        </button>
                    </td>
                    <td class="text-center">
                        <button class="btn btn-sm btn-link text-info" data-node='${encodeURIComponent(JSON.stringify(node))}' onclick="openEditNodeModal(this)">
                            <i class="bi bi-pencil fs-5"></i>
                        </button>
                        <button class="btn btn-sm btn-link text-danger" data-node-id="${node.id}" onclick="openDeleteNodeModal(this)">
                            <i class="bi bi-trash fs-5"></i>
                        </button>
                    </td>
                </tr>
            `;
        });

        tbody.innerHTML = nodesHtml;
    } catch (error) {
        console.error('Error updating nodes table:', error);
        tbody.innerHTML = `
            <tr>
                <td colspan="7" class="text-center">
                    <div class="alert alert-danger mb-0">
                        Lỗi hiển thị dữ liệu: ${error.message}
                        <button class="btn btn-link p-0 ms-2" onclick="loadNodes()">
                            Thử lại
                        </button>
                    </div>
                </td>
            </tr>
        `;
    }
}

// Open the manual check modal
function openCheckConfigModal(nodeId) {
    try {
        const modal = new bootstrap.Modal(document.getElementById('checkConfigModal'));
        document.getElementById('checkConfigNodeId').value = nodeId;
        document.getElementById('checkConfigResult').innerHTML = 'Chưa kiểm tra.';
        modal.show();
    } catch (error) {
        console.error('Error opening config modal:', error);
        alert('Không thể mở form kiểm tra cấu hình');
    }
}

// Perform manual check
async function performManualCheck() {
    const nodeId = document.getElementById('checkConfigNodeId').value;
    const resultContainer = document.getElementById('checkConfigResult');
    resultContainer.textContent = 'Đang kiểm tra...';

    try {
        const response = await fetch(`/api/nodes/${nodeId}/metrics`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
            }
        });

        if (!response.ok) {
            throw new Error('Failed to fetch metrics');
        }

        const metrics = await response.json();
        resultContainer.innerHTML = `
            <p>NodeExporter: ${metrics.nodeExporter}</p>
            <p>Promtail: ${metrics.promtail}</p>
        `;
    } catch (error) {
        console.error('Error performing manual check:', error);
        resultContainer.textContent = 'Không thể kiểm tra cấu hình.';
    }
}

async function saveNode() {
    const token = localStorage.getItem('auth_token');
    const name = document.getElementById('nodeName').value;
    const ipAddress = document.getElementById('nodeIp').value;
    const portNodeExporter = parseInt(document.getElementById('portNodeExporter').value);
    const portPromtail = parseInt(document.getElementById('portPromtail').value);

    try {
        const response = await fetch('/api/nodes', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + token
            },
            body: JSON.stringify({ 
                name, 
                ipAddress, 
                portNodeExporter,
                portPromtail,
                status: 'inactive' // Default status for new nodes
            })
        });

        if (!response.ok) {
            throw new Error('Failed to add node');
        }

        // Close modal and reload nodes
        bootstrap.Modal.getInstance(document.getElementById('addNodeModal')).hide();
        document.getElementById('addNodeForm').reset();
        loadNodes();

    } catch (error) {
        console.error('Error:', error);
        alert('Không thể thêm node mới');
    }
}

function logout() {
    localStorage.removeItem('auth_token');
    window.location.href = '/auth/login';
}

async function deleteNode(nodeId) {
    try {
        const response = await fetch(`/api/nodes/${nodeId}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
            }
        });

        if (!response.ok) {
            throw new Error('Failed to delete node');
        }

        await loadNodes();
        const deleteModal = bootstrap.Modal.getInstance(document.getElementById('deleteNodeModal'));
        deleteModal.hide();
    } catch (error) {
        console.error('Error deleting node:', error);
        alert('Không thể xóa node');
    }
}

function viewNodeDetails(nodeId) {
    window.location.href = `/dashboard/nodes/${nodeId}`;
}

// Open the edit modal and populate the form
function openEditNodeModal(button) {
    try {
        const nodeData = JSON.parse(decodeURIComponent(button.getAttribute('data-node')));
        const editForm = document.getElementById('editNodeForm');
        
        document.getElementById('editNodeId').value = nodeData.id;
        document.getElementById('editNodeName').value = nodeData.name || '';
        document.getElementById('editNodeIp').value = nodeData.ipAddress || '';
        document.getElementById('editPortNodeExporter').value = nodeData.portNodeExporter || '';
        document.getElementById('editPortPromtail').value = nodeData.portPromtail || '';
        
        const editModal = new bootstrap.Modal(document.getElementById('editNodeModal'));
        editModal.show();
    } catch (error) {
        console.error('Error opening edit modal:', error);
        alert('Không thể mở form chỉnh sửa');
    }
}

// Save the edited node
async function saveEditedNode() {
    try {
        const nodeId = document.getElementById('editNodeId').value;
        const updatedNode = {
            name: document.getElementById('editNodeName').value,
            ipAddress: document.getElementById('editNodeIp').value,
            portNodeExporter: parseInt(document.getElementById('editPortNodeExporter').value),
            portPromtail: parseInt(document.getElementById('editPortPromtail').value)
        };

        const response = await fetch(`/api/nodes/${nodeId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
            },
            body: JSON.stringify(updatedNode)
        });

        if (!response.ok) {
            throw new Error('Failed to update node');
        }

        await loadNodes();
        const editModal = bootstrap.Modal.getInstance(document.getElementById('editNodeModal'));
        editModal.hide();
    } catch (error) {
        console.error('Error updating node:', error);
        alert('Không thể cập nhật node');
    }
}

function setupEventHandlers() {
    // Handle pin buttons
    document.querySelectorAll('.pin-node').forEach(button => {
        button.addEventListener('click', function() {
            const nodeId = parseInt(this.getAttribute('data-node-id'));
            const pinnedNodes = JSON.parse(localStorage.getItem('pinnedNodes')) || [];
            const isPinned = pinnedNodes.includes(nodeId);
            
            if (isPinned) {
                // Unpin node
                const index = pinnedNodes.indexOf(nodeId);
                pinnedNodes.splice(index, 1);
                this.querySelector('i').classList.replace('bi-pin-fill', 'bi-pin');
                document.querySelector(`#nodeDetails${nodeId}`).classList.remove('show');
                document.querySelector(`[data-bs-target="#nodeDetails${nodeId}"] i`).classList.replace('bi-chevron-up', 'bi-chevron-down');
            } else {
                // Pin node
                pinnedNodes.push(nodeId);
                this.querySelector('i').classList.replace('bi-pin', 'bi-pin-fill');
                document.querySelector(`#nodeDetails${nodeId}`).classList.add('show');
                document.querySelector(`[data-bs-target="#nodeDetails${nodeId}"] i`).classList.replace('bi-chevron-down', 'bi-chevron-up');
            }
            
            localStorage.setItem('pinnedNodes', JSON.stringify(pinnedNodes));
        });
    });

    // Handle collapse buttons
    document.querySelectorAll('.toggle-collapse').forEach(button => {
        button.addEventListener('click', function() {
            const icon = this.querySelector('i');
            const nodeId = parseInt(this.getAttribute('data-bs-target').replace('#nodeDetails', ''));
            const pinnedNodes = JSON.parse(localStorage.getItem('pinnedNodes')) || [];
            const isPinned = pinnedNodes.includes(nodeId);
            
            if (icon.classList.contains('bi-chevron-down')) {
                icon.classList.replace('bi-chevron-down', 'bi-chevron-up');
            } else {
                icon.classList.replace('bi-chevron-up', 'bi-chevron-down');
                if (isPinned) {
                    // Remove from pinned if it was pinned
                    const index = pinnedNodes.indexOf(nodeId);
                    pinnedNodes.splice(index, 1);
                    document.querySelector(`[data-node-id="${nodeId}"] i`).classList.replace('bi-pin-fill', 'bi-pin');
                    localStorage.setItem('pinnedNodes', JSON.stringify(pinnedNodes));
                }
            }
        });
    });
}

// Open the delete confirmation modal
function openDeleteNodeModal(button) {
    try {
        const nodeId = button.getAttribute('data-node-id');
        const deleteButton = document.getElementById('confirmDeleteNodeButton');
        if (!deleteButton) {
            throw new Error('Delete button not found');
        }
        
        deleteButton.setAttribute('data-node-id', nodeId);
        const deleteModal = new bootstrap.Modal(document.getElementById('deleteNodeModal'));
        deleteModal.show();
    } catch (error) {
        console.error('Error opening delete modal:', error);
        alert('Không thể mở form xóa');
    }
}

// Open the Add Alert Modal
function openAddAlertModal(nodeId) {
    try {
        const modal = new bootstrap.Modal(document.getElementById('addAlertModal'));
        document.getElementById('alertNodeId').value = nodeId;
        modal.show();
    } catch (error) {
        console.error('Error opening alert modal:', error);
        alert('Không thể mở form thêm cảnh báo');
    }
}

// Save the Alert
async function saveAlert() {
    try {
        const nodeId = document.getElementById('alertNodeId').value;
        const message = document.getElementById('alertMessage').value;
        const destination = document.getElementById('alertDestination').value;

        if (!message || !destination) {
            alert('Vui lòng điền đầy đủ thông tin');
            return;
        }

        console.log('Sending alert data:', { nodeId, message, destination }); // Debug log

        const response = await fetch(`/api/nodes/${nodeId}/alerts`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
            },
            body: JSON.stringify({ message, destination })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to create alert');
        }

        // Close modal and reload nodes
        const modal = bootstrap.Modal.getInstance(document.getElementById('addAlertModal'));
        modal.hide();
        await loadNodes();
        
    } catch (error) {
        console.error('Error saving alert:', error);
        alert('Không thể thêm cảnh báo: ' + error.message);
    }
}
// Kiểm tra xem người dùng đã đăng nhập chưa
document.addEventListener('DOMContentLoaded', function () {
    const token = localStorage.getItem('auth_token');
    if (!token) {
        window.location.href = '/auth/login';
        return;
    }

    // Load dashboard data
    loadDashboardData();

    // Handle logout
    document.getElementById('logout-btn').addEventListener('click', function (event) {
        event.preventDefault();
        localStorage.removeItem('auth_token');
        window.location.href = '/auth/login';
    });
});

// Tải dữ liệu dashboard
function loadDashboardData() {
    const token = localStorage.getItem('auth_token');
    
    // Fetch all nodes
    fetch('/api/nodes', {
        headers: {
            'Authorization': 'Bearer ' + token
        }
    })
    .then(response => {
        if (!response.ok) {
            if (response.status === 401) {
                localStorage.removeItem('auth_token');
                window.location.href = '/auth/login';
            }
            throw new Error('Không thể tải dữ liệu');
        }
        return response.json();
    })
    .then(nodes => {
        // Update node statistics
        const totalNodes = nodes.length;
        const activeNodes = nodes.filter(node => node.status === 'active').length;
        const inactiveNodes = nodes.filter(node => node.status !== 'active').length;

        // Update statistics display
        document.getElementById('total-nodes').textContent = totalNodes;
        document.getElementById('active-nodes').textContent = activeNodes;
        document.getElementById('inactive-nodes').textContent = inactiveNodes;

        // Display nodes in table
        const nodesElement = document.getElementById('recent-nodes');
        
        if (nodes.length === 0) {
            nodesElement.innerHTML = `
                <tr>
                    <td colspan="5" class="text-center">Chưa có Nodes nào</td>
                </tr>
            `;
            return;
        }
        
        let nodesHtml = '';
        nodes.forEach((node, index) => {
            const statusClass = node.status === 'active' ? 'success' : 'danger';
            const statusText = node.status === 'active' ? 'Hoạt động' : 'Không hoạt động';
            const pinnedNodes = JSON.parse(localStorage.getItem('pinnedNodes')) || [];
            const isPinned = pinnedNodes.includes(node.id);
            
            nodesHtml += `
                <tr>
                    <td>${index + 1}</td>
                    <td>${node.name}</td>
                    <td>${node.ipAddress}</td>
                    <td><span class="badge bg-${statusClass}">${statusText}</span></td>
                    <td class="text-center">
                        <button class="btn btn-sm btn-link text-primary toggle-collapse" 
                                data-bs-toggle="collapse" 
                                data-bs-target="#nodeDetails${node.id}" 
                                aria-expanded="${isPinned ? 'true' : 'false'}">
                            <i class="bi ${isPinned ? 'bi-chevron-up' : 'bi-chevron-down'} fs-5"></i>
                        </button>
                        <button class="btn btn-sm btn-link text-warning pin-node" data-node-id="${node.id}">
                            <i class="bi ${isPinned ? 'bi-pin-fill' : 'bi-pin'} fs-5"></i>
                        </button>
                    </td>
                </tr>
                <tr class="collapse ${isPinned ? 'show' : ''}" id="nodeDetails${node.id}">
                    <td colspan="5">
                        <div class="card card-body">
                            <div class="row">
                                <div class="col-md-6">
                                    <p><strong>Node Exporter Port:</strong> ${node.portNodeExporter}</p>
                                    <p><strong>Promtail Port:</strong> ${node.portPromtail}</p>
                                    <p><strong>Status:</strong> <span class="badge bg-${statusClass}">${statusText}</span></p>
                                </div>
                                <div class="col-md-6">
                                    <p><strong>IP Address:</strong> ${node.ipAddress}</p>
                                    <p><strong>Name:</strong> ${node.name}</p>
                                    <p><strong>ID:</strong> ${node.id}</p>
                                </div>
                            </div>
                        </div>
                    </td>
                </tr>
            `;
        });
        
        nodesElement.innerHTML = nodesHtml;

        // Add event handlers for pin and collapse buttons
        setupEventHandlers();
    })
    .catch(error => {
        console.error('Error:', error);
        // Show error in statistics cards
        document.getElementById('total-nodes').textContent = 'Lỗi';
        document.getElementById('active-nodes').textContent = 'Lỗi';
        document.getElementById('inactive-nodes').textContent = 'Lỗi';
    });
}

// Setup event handlers for pin and collapse buttons
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
            if (icon.classList.contains('bi-chevron-down')) {
                icon.classList.replace('bi-chevron-down', 'bi-chevron-up');
            } else {
                icon.classList.replace('bi-chevron-up', 'bi-chevron-down');
            }
        });
    });
}
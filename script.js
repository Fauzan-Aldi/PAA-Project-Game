class SelfDrivingCarAI {
    constructor() {
        this.canvas = document.getElementById('mapCanvas');
        this.ctx = this.canvas.getContext('2d');
        this.mapImage = null;
        this.imageData = null;
        this.roadPixels = [];
        this.car = { x: 0, y: 0, angle: 0, size: 15 };
        this.target = { x: 0, y: 0, size: 8 };
        this.path = [];
        this.pathIndex = 0;
        this.isMoving = false;
        this.animationId = null;
        
        this.initEventListeners();
        this.updateStatus('Ready to upload map', 'ready');
    }

    initEventListeners() {
        const mapInput = document.getElementById('mapInput');
        const fileWrapper = mapInput.parentElement;
        
        // Multiple event listeners for better compatibility
        mapInput.addEventListener('change', (e) => this.handleMapUpload(e));
        
        // Add click handler to wrapper as backup
        fileWrapper.addEventListener('click', (e) => {
            if (e.target !== mapInput) {
                e.preventDefault();
                mapInput.click();
            }
        });
        
        document.getElementById('randomizeBtn').addEventListener('click', () => this.randomizePositions());
        document.getElementById('analyzeBtn').addEventListener('click', () => this.analyzePath());
        document.getElementById('startBtn').addEventListener('click', () => this.startNavigation());
        document.getElementById('resetBtn').addEventListener('click', () => this.reset());
    }

    updateStatus(message, type = 'ready') {
        const statusElement = document.getElementById('systemStatus');
        const indicator = statusElement.querySelector('.status-indicator');
        
        indicator.className = `status-indicator status-${type}`;
        statusElement.innerHTML = `<span class="status-indicator status-${type}"></span>${message}`;
    }

    updateProgress(percent) {
        document.getElementById('progressFill').style.width = `${percent}%`;
    }

    async handleMapUpload(event) {
        const file = event.target.files[0];
        if (!file) {
            console.log('No file selected');
            return;
        }

        console.log('File selected:', file.name, file.type, file.size);
        
        if (!file.type.startsWith('image/')) {
            alert('Please select a valid image file!');
            return;
        }

        this.updateStatus('Loading map image...', 'processing');
        this.updateProgress(25);

        try {
            const img = new Image();
            img.onload = () => {
                console.log('Image loaded successfully:', img.width, 'x', img.height);
                this.mapImage = img;
                this.canvas.width = Math.min(800, img.width);
                this.canvas.height = Math.min(800, img.height);
                
                this.ctx.drawImage(img, 0, 0, this.canvas.width, this.canvas.height);
                this.imageData = this.ctx.getImageData(0, 0, this.canvas.width, this.canvas.height);
                
                this.updateProgress(75);
                this.analyzeRoads();
                this.updateProgress(100);
                
                this.updateStatus('Map loaded successfully!', 'ready');
                document.getElementById('randomizeBtn').disabled = false;
                
                setTimeout(() => this.updateProgress(0), 2000);
            };

            img.onerror = () => {
                console.error('Failed to load image');
                this.updateStatus('Failed to load image!', 'error');
                alert('Failed to load the selected image. Please try another file.');
            };

            const reader = new FileReader();
            reader.onload = (e) => {
                console.log('FileReader loaded successfully');
                img.src = e.target.result;
            };
            
            reader.onerror = () => {
                console.error('FileReader error');
                this.updateStatus('Failed to read file!', 'error');
                alert('Failed to read the selected file.');
            };
            
            reader.readAsDataURL(file);
        } catch (error) {
            console.error('Error in handleMapUpload:', error);
            this.updateStatus('Upload failed!', 'error');
            alert('An error occurred while uploading the file.');
        }
    }

    analyzeRoads() {
        this.roadPixels = [];
        const data = this.imageData.data;
        let roadCount = 0;

        for (let y = 0; y < this.canvas.height; y++) {
            for (let x = 0; x < this.canvas.width; x++) {
                const index = (y * this.canvas.width + x) * 4;
                const r = data[index];
                const g = data[index + 1];
                const b = data[index + 2];

                // Check if pixel is road (gray colors between rgb(90,90,90) and rgb(150,150,150))
                if (r >= 90 && r <= 150 && g >= 90 && g <= 150 && b >= 90 && b <= 150) {
                    this.roadPixels.push({ x, y });
                    roadCount++;
                }
            }
        }

        document.getElementById('roadCount').textContent = roadCount.toLocaleString();
        this.updateStatus(`Analyzed ${roadCount.toLocaleString()} road pixels`, 'ready');
    }

    randomizePositions() {
        if (this.roadPixels.length < 2) {
            alert('Not enough road pixels detected!');
            return;
        }

        this.updateStatus('Randomizing positions...', 'processing');

        // Place car randomly on road
        const carIndex = Math.floor(Math.random() * this.roadPixels.length);
        this.car.x = this.roadPixels[carIndex].x;
        this.car.y = this.roadPixels[carIndex].y;
        this.car.angle = 0;

        // Place target randomly on road (different from car)
        let targetIndex;
        do {
            targetIndex = Math.floor(Math.random() * this.roadPixels.length);
        } while (targetIndex === carIndex);
        
        this.target.x = this.roadPixels[targetIndex].x;
        this.target.y = this.roadPixels[targetIndex].y;

        this.updateDisplay();
        this.updateNavigationInfo();
        this.updateStatus('Positions randomized successfully!', 'ready');
        
        document.getElementById('analyzeBtn').disabled = false;
    }

    analyzePath() {
        this.updateStatus('Analyzing optimal path...', 'processing');
        this.updateProgress(0);

        setTimeout(() => {
            this.path = this.findPath(this.car, this.target);
            this.drawPath();
            this.updateProgress(100);
            this.updateStatus('Path analysis complete!', 'ready');
            document.getElementById('startBtn').disabled = false;
            
            setTimeout(() => this.updateProgress(0), 2000);
        }, 500);
    }

    findPath(start, end) {
        // Simplified A* pathfinding for road pixels
        const path = [];
        const visited = new Set();
        const queue = [{ x: start.x, y: start.y, path: [{ x: start.x, y: start.y }] }];

        while (queue.length > 0) {
            queue.sort((a, b) => {
                const distA = Math.sqrt((a.x - end.x) ** 2 + (a.y - end.y) ** 2);
                const distB = Math.sqrt((b.x - end.x) ** 2 + (b.y - end.y) ** 2);
                return distA - distB;
            });

            const current = queue.shift();
            const key = `${current.x},${current.y}`;

            if (visited.has(key)) continue;
            visited.add(key);

            if (Math.abs(current.x - end.x) < 5 && Math.abs(current.y - end.y) < 5) {
                return current.path;
            }

            // Add neighboring road pixels
            for (let dx = -3; dx <= 3; dx += 3) {
                for (let dy = -3; dy <= 3; dy += 3) {
                    if (dx === 0 && dy === 0) continue;
                    
                    const newX = current.x + dx;
                    const newY = current.y + dy;
                    const newKey = `${newX},${newY}`;

                    if (!visited.has(newKey) && this.isRoadPixel(newX, newY)) {
                        queue.push({
                            x: newX,
                            y: newY,
                            path: [...current.path, { x: newX, y: newY }]
                        });
                    }
                }
            }

            if (current.path.length > 500) break; // Prevent infinite loops
        }

        // Fallback: direct line with road following
        return this.createDirectPath(start, end);
    }

    createDirectPath(start, end) {
        const path = [];
        const steps = Math.max(Math.abs(end.x - start.x), Math.abs(end.y - start.y));
        
        for (let i = 0; i <= steps; i += 5) {
            const progress = i / steps;
            const x = Math.round(start.x + (end.x - start.x) * progress);
            const y = Math.round(start.y + (end.y - start.y) * progress);
            
            // Try to snap to nearest road pixel
            const roadPixel = this.findNearestRoadPixel(x, y);
            if (roadPixel) {
                path.push(roadPixel);
            }
        }
        
        return path;
    }

    findNearestRoadPixel(x, y) {
        let minDist = Infinity;
        let nearest = null;

        for (const pixel of this.roadPixels) {
            const dist = Math.sqrt((pixel.x - x) ** 2 + (pixel.y - y) ** 2);
            if (dist < minDist && dist < 20) {
                minDist = dist;
                nearest = pixel;
            }
        }

        return nearest || { x, y };
    }

    isRoadPixel(x, y) {
        if (x < 0 || x >= this.canvas.width || y < 0 || y >= this.canvas.height) return false;
        
        const index = (y * this.canvas.width + x) * 4;
        const r = this.imageData.data[index];
        const g = this.imageData.data[index + 1];
        const b = this.imageData.data[index + 2];

        return r >= 90 && r <= 150 && g >= 90 && g <= 150 && b >= 90 && b <= 150;
    }

    drawPath() {
        this.updateDisplay();
        
        if (this.path.length > 1) {
            this.ctx.strokeStyle = 'rgba(255, 255, 0, 0.6)';
            this.ctx.lineWidth = 3;
            this.ctx.setLineDash([5, 5]);
            this.ctx.beginPath();
            
            this.ctx.moveTo(this.path[0].x, this.path[0].y);
            for (let i = 1; i < this.path.length; i++) {
                this.ctx.lineTo(this.path[i].x, this.path[i].y);
            }
            this.ctx.stroke();
            this.ctx.setLineDash([]);
        }
    }

    startNavigation() {
        if (this.path.length === 0) {
            alert('Please analyze path first!');
            return;
        }

        this.isMoving = true;
        this.pathIndex = 0;
        this.updateStatus('Navigation in progress...', 'processing');
        document.getElementById('startBtn').disabled = true;
        
        this.animate();
    }

    animate() {
        if (!this.isMoving || this.pathIndex >= this.path.length - 1) {
            this.reachTarget();
            return;
        }

        const currentTarget = this.path[this.pathIndex + 1];
        const dx = currentTarget.x - this.car.x;
        const dy = currentTarget.y - this.car.y;
        const distance = Math.sqrt(dx * dx + dy * dy);

        if (distance < 2) {
            this.pathIndex++;
        } else {
            // Move car towards next point
            const speed = 2;
            this.car.x += (dx / distance) * speed;
            this.car.y += (dy / distance) * speed;
            
            // Update car angle
            this.car.angle = Math.atan2(dy, dx);
        }

        this.updateDisplay();
        this.updateNavigationInfo();
        
        this.animationId = requestAnimationFrame(() => this.animate());
    }

    reachTarget() {
        this.isMoving = false;
        this.updateStatus('Target reached successfully!', 'ready');
        document.getElementById('startBtn').disabled = false;
        
        // Show success alert
        const alert = document.createElement('div');
        alert.className = 'alert';
        alert.textContent = '🎉 Mobil sampai ke target!';
        document.body.appendChild(alert);

        setTimeout(() => {
            document.body.removeChild(alert);
        }, 3000);
    }

    updateDisplay() {
        if (!this.mapImage) return;

        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        this.ctx.drawImage(this.mapImage, 0, 0, this.canvas.width, this.canvas.height);

        // Draw target
        this.ctx.fillStyle = '#ff0000';
        this.ctx.beginPath();
        this.ctx.arc(this.target.x, this.target.y, this.target.size, 0, Math.PI * 2);
        this.ctx.fill();

        // Draw car (triangle)
        this.ctx.save();
        this.ctx.translate(this.car.x, this.car.y);
        this.ctx.rotate(this.car.angle);
        
        this.ctx.fillStyle = '#00ff00';
        this.ctx.beginPath();
        this.ctx.moveTo(this.car.size, 0);
        this.ctx.lineTo(-this.car.size / 2, -this.car.size / 2);
        this.ctx.lineTo(-this.car.size / 2, this.car.size / 2);
        this.ctx.closePath();
        this.ctx.fill();
        
        this.ctx.strokeStyle = '#000000';
        this.ctx.lineWidth = 2;
        this.ctx.stroke();
        
        this.ctx.restore();
    }

    updateNavigationInfo() {
        document.getElementById('carPos').textContent = `(${Math.round(this.car.x)}, ${Math.round(this.car.y)})`;
        document.getElementById('targetPos').textContent = `(${this.target.x}, ${this.target.y})`;
        
        const distance = Math.sqrt((this.target.x - this.car.x) ** 2 + (this.target.y - this.car.y) ** 2);
        document.getElementById('distance').textContent = `${Math.round(distance)}px`;
    }

    reset() {
        if (this.animationId) {
            cancelAnimationFrame(this.animationId);
        }
        
        this.isMoving = false;
        this.path = [];
        this.pathIndex = 0;
        this.car = { x: 0, y: 0, angle: 0, size: 15 };
        this.target = { x: 0, y: 0, size: 8 };
        
        document.getElementById('mapInput').value = '';
        document.getElementById('randomizeBtn').disabled = true;
        document.getElementById('analyzeBtn').disabled = true;
        document.getElementById('startBtn').disabled = true;
        
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        this.updateStatus('System reset - Ready to upload map', 'ready');
        this.updateProgress(0);
        
        document.getElementById('carPos').textContent = 'Not placed';
        document.getElementById('targetPos').textContent = 'Not placed';
        document.getElementById('distance').textContent = '-';
        document.getElementById('roadCount').textContent = '0';
    }
}

// Initialize the system
window.addEventListener('DOMContentLoaded', () => {
    new SelfDrivingCarAI();
});

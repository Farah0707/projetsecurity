const canvas = document.getElementById('bg-canvas');
const ctx = canvas.getContext('2d');
canvas.width = window.innerWidth;
canvas.height = window.innerHeight;

const particles = [];
const particleCount = 80;

for(let i=0; i<particleCount; i++){
    particles.push({
        x: Math.random()*canvas.width,
        y: Math.random()*canvas.height,
        vx: (Math.random()-0.5)*0.5,
        vy: (Math.random()-0.5)*0.5,
        size: Math.random()*3+1
    });
}

function animate(){
    ctx.clearRect(0,0,canvas.width, canvas.height);
    ctx.fillStyle = '#00ffe5';

    particles.forEach(p => {
        p.x += p.vx;
        p.y += p.vy;

        if(p.x<0 || p.x>canvas.width) p.vx *= -1;
        if(p.y<0 || p.y>canvas.height) p.vy *= -1;

        ctx.beginPath();
        ctx.arc(p.x,p.y,p.size,0,Math.PI*2);
        ctx.fill();
    });

    for(let i=0;i<particles.length;i++){
        for(let j=i+1;j<particles.length;j++){
            let dx = particles[i].x - particles[j].x;
            let dy = particles[i].y - particles[j].y;
            let dist = Math.sqrt(dx*dx + dy*dy);
            if(dist<100){
                ctx.strokeStyle = 'rgba(0,255,229,'+(1-dist/100)+')';
                ctx.lineWidth = 1;
                ctx.beginPath();
                ctx.moveTo(particles[i].x,particles[i].y);
                ctx.lineTo(particles[j].x,particles[j].y);
                ctx.stroke();
            }
        }
    }

    requestAnimationFrame(animate);
}

animate();

window.addEventListener('resize', ()=>{
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
});

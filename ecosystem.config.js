module.exports = {
  apps: [{
    name: 'mmai-v2',
    script: '.venv/bin/uvicorn',
    args: 'app.main:app --host 127.0.0.1 --port 8001 --workers 2',
    cwd: '/home/mmai/mmai-v2/backend',
    interpreter: 'none',
    instances: 1,
    exec_mode: 'fork',
    max_memory_restart: '512M',

    autorestart: true,
    max_restarts: 10,
    min_uptime: '30s',
    restart_delay: 4000,

    error_file: '/home/mmai/mmai-v2/logs/error.log',
    out_file: '/home/mmai/mmai-v2/logs/out.log',
    merge_logs: true,
    time: true,
    log_date_format: 'YYYY-MM-DD HH:mm:ss Z',

    env: {
      NODE_ENV: 'production'
    },

    watch: false
  }]
};

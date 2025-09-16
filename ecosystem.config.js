module.exports = {
  apps: [
    {
      name: 'receipts-bot',
      script: 'bot/main.py',
      interpreter: 'python3',
      cwd: '/path/to/your/receipts_bot',
      env: {
        PYTHONPATH: '/path/to/your/receipts_bot',
        DJANGO_SETTINGS_MODULE: 'receipts_project.settings'
      },
      error_file: './logs/err.log',
      out_file: './logs/out.log',
      log_file: './logs/combined.log',
      time: true,
      autorestart: true,
      watch: false,
      max_memory_restart: '1G',
      exec_mode: 'fork',
      instances: 1
    }
  ]
};
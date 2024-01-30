from flask import Flask, render_template, request, session, Response
import paramiko

app = Flask(__name__)
app.secret_key = '123456'


def create_ssh_client(ip, port, username, password):
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(ip, port=port, username=username, password=password)
        return client
    except Exception as e:
        print(f"连接错误: {e}")
        return None


def exec_ssh_command(client, command):
    stdin, stdout, stderr = client.exec_command(command)
    return stdout.read().decode('utf-8')


@app.route('/', methods=['GET', 'POST'])
def index():
    message = ''
    system_info = None

    if request.method == 'POST':
        session['ip'] = request.form.get('ip')
        session['port'] = int(request.form.get('port'))
        session['username'] = request.form.get('username')
        session['password'] = request.form.get('password')

        client = create_ssh_client(session['ip'], session['port'], session['username'], session['password'])
        if client:
            if 'start' in request.form:
                # 这里单独运行，否则会一直阻塞程序
                stdin, stdout, stderr = client.exec_command(
                    'nohup sudo -u steam bash /home/steam/.steam/SteamApps/common/PalServer/PalServer.sh &')
                stdin.close()
                stdout.close()
                stderr.close()
                message = "服务器已启动。"
            elif 'stop' in request.form:
                exec_ssh_command(client, 'pkill -f PalServer-Linux-Test')
                message = "服务器已关闭。"
            elif 'gx' in request.form:
                exec_ssh_command(client,
                                 'wget http://172.168.0.12:88/scripts/update.sh -O update.sh && chmod +x update.sh && bash update.sh')
                message = "更新游戏版本成功"
            elif 'config' in request.form:
                sftp = client.open_sftp()
                remote_file = sftp.file(
                    '/home/steam/.steam/SteamApps/common/PalServer/Pal/Saved/Config/LinuxServer/PalWorldSettings.ini',
                    'r')
                file_content = remote_file.read()
                sftp.close()
                return Response(file_content, mimetype='text/plain',
                                headers={"Content-disposition": "attachment; filename=PalWorldSettings.ini"})
            elif 'get_sys_info' in request.form:
                cpu_usage = exec_ssh_command(client, "top -bn1 | grep 'Cpu(s)' | awk '{print $2}'")
                total_memory, used_memory = exec_ssh_command(client, "free -m | awk 'NR==2{print $2,$3}'").split()
                disk_usage = exec_ssh_command(client, "df -h | awk '$NF==\"/\"{print $5}'")
                total_disk = exec_ssh_command(client, "df -h | awk '$NF==\"/\"{print $2}'")
                used_disk = exec_ssh_command(client, "df -h | awk '$NF==\"/\"{print $3}'")

                pal_server_memory_usage = exec_ssh_command(client,
                                                           "ps -aux | grep PalServer-Linux-Test | awk '{print $6/1024}' | head -n 1")
                if pal_server_memory_usage.strip():
                    pal_server_memory_usage = f'{float(pal_server_memory_usage.strip()):.2f} MB'
                else:
                    pal_server_memory_usage = '未运行'

                message = "获取服务器信息成功"
                system_info = {
                    'cpu_usage': f'{cpu_usage.strip()}%',
                    'memory': f'{float(used_memory) / float(total_memory) * 100:.2f}%',
                    'total_memory': f'{total_memory} MB',
                    'used_memory': f'{used_memory} MB',
                    'disk': disk_usage.strip(),
                    'total_disk': total_disk.strip(),
                    'used_disk': used_disk.strip(),
                    'pal_server_memory_usage': pal_server_memory_usage.strip(),
                }
            elif 'upload_config' in request.form:
                uploaded_file = request.files['config_data']
                if uploaded_file.filename == '':
                    message = "请选择文件。"
                    return render_template('index.html', message=message)
                exec_ssh_command(client, 'pkill -f PalServer-Linux-Test')
                sftp = client.open_sftp()
                remote_file = sftp.file(
                    '/home/steam/.steam/SteamApps/common/PalServer/Pal/Saved/Config/LinuxServer/PalWorldSettings.ini',
                    'w')
                remote_file.write(uploaded_file.stream.read())
                remote_file.close()
                sftp.close()
                # 这里单独运行，否则会一直阻塞程序
                stdin, stdout, stderr = client.exec_command(
                    'nohup sudo -u steam bash /home/steam/.steam/SteamApps/common/PalServer/PalServer.sh &')
                stdin.close()
                stdout.close()
                stderr.close()
                message = "配置文件已上传。"
            client.close()
        else:
            message = "连接失败。"

    return render_template('index.html', message=message, system_info=system_info)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8211)

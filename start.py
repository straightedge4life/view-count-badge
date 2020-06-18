from socket import *
import xml.etree.ElementTree as Et
import redis
import os


def recv_request(connection):
    """
    处理请求头信息
    :param connection:
    :return: headers:头信息(集合) params:传递的参数(字典)
    """
    headers_raw = connection.recv(1024).decode().split('\r\n')
    request_info = headers_raw.pop(0).split(' ')
    params = {}
    for query in request_info[1].replace('/?', '').split('&'):
        if query and query is not '/':
            kv_set = query.split('=')
            if len(kv_set) > 1:
                params[query.split('=')[0]] = query.split('=')[1]

    headers = (row.replace('\r\n', '') for row in headers_raw)
    return headers, params


def edit_svg(key):
    """
    使用redis保存观看数字 并更改svg文件
    :param key:
    :return:
    """
    view_num = 1
    svg_file = os.path.dirname(__file__) + '/view.svg'
    tree = Et.parse(svg_file)
    root = tree.getroot()

    if key:
        r_conn = redis.Redis(host="127.0.0.1", port=6379, password="")
        val = r_conn.get(key)

        if val:
            view_num = int(val) + 1
            r_conn.set(key, view_num)
        else:
            r_conn.set(key, 1)

    root[3][2].text = str(view_num)
    root[3][3].text = str(view_num)

    Et.register_namespace('', "http://www.w3.org/2000/svg")
    tree.write(svg_file)
    with open(svg_file, 'rb') as f:
        svg_string = f.read()
    return svg_string.decode()


server_port = 12000
server_host = '127.0.0.1'


with socket(AF_INET, SOCK_STREAM) as s:
    s.bind((server_host, server_port))
    s.listen(10)

    while True:
        conn, addr = s.accept()
        request_headers, params = recv_request(conn)
        body = edit_svg(params.get('key'))
        response_header = 'Content-type: image/svg+xml; encoding=utf-8\nContent-Length: ' + str(len(body)) + '\n'
        status = 'HTTP/1.1 200 OK \n'
        conn.send(status.encode())
        conn.send(response_header.encode())
        conn.send('\n'.encode())
        conn.send(body.encode())
        conn.close()


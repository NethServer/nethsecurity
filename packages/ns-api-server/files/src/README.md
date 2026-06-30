# nethsecurity-api

## Build
```bash
CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build
```

## Run
```bash
SECRET_JWT="<secret>" SECRETS_DIR="<secrets_dir>" TOKENS_DIR="<tokens_dir>" ./nethsecurity-api
```

Where:
- `SECRET_JWT`: is the secret used to sign JWT tokens
- `SECRETS_DIR`: is the directory where 2FA secrets are stored, must be persistent
- `TOKENS_DIR`: is the directory where valid JWT tokens are stored

## APIs
### Auth
- `POST /api/login`

    REQ
    ```json
     Content-Type: application/json

     {
       "username": "root",
       "password": "Nethesis,1234"
     }
    ```

    RES
    ```json
     HTTP/1.1 200 OK
     Content-Type: application/json; charset=utf-8

     {
       "code": 200,
       "expire": "2023-05-25T14:04:03.734920987Z",
       "token": "eyJh...E-f0"
     }
    ```
- `POST /api/logout`

    REQ
    ```json
     Content-Type: application/json
     Authorization: Bearer <JWT_TOKEN>
    ```

    RES
    ```json
     HTTP/1.1 200 OK
     Content-Type: application/json; charset=utf-8

     {
       "code": 200
     }
    ```
- `GET /api/refresh`

    REQ
    ```json
     Content-Type: application/json
     Authorization: Bearer <JWT_TOKEN>
    ```

    RES
    ```json
     HTTP/1.1 200 OK
     Content-Type: application/json; charset=utf-8

     {
       "code": 200,
       "expire": "2023-05-25T14:04:03.734920987Z",
       "token": "eyJh...E-f0"
     }
    ```

### 2FA
- `POST /api/2fa/otp-verify`

    REQ
    ```json
     Content-Type: application/json
     Authorization: Bearer <JWT_TOKEN>

     {
       "username": "root",
       "token": "eyJhbGc...VXT7l0",
       "otp": "435450"
     }
    ```

    RES
    ```json
     HTTP/1.1 200 OK
     Content-Type: application/json; charset=utf-8

     {
       "code": 200,
       "data": "eyJhbGc...VXT7l0",
       "message": "OTP verified"
     }
    ```

- `GET /api/2fa`

    REQ
    ```json
     Content-Type: application/json
     Authorization: Bearer <JWT_TOKEN>
    ```

    RES
    ```json
     HTTP/1.1 200 OK
     Content-Type: application/json; charset=utf-8

     {
       "code": 200,
       "data": false,
       "message": "2FA not set for this user"
     }
    ```
- `DELETE /api/2fa`

    REQ
    ```json
     Content-Type: application/json
     Authorization: Bearer <JWT_TOKEN>
    ```

    RES
    ```json
     HTTP/1.1 200 OK
     Content-Type: application/json; charset=utf-8

     {
       "code": 200,
       "data": false,
       "message": "2FA revocate successfully"
     }
    ```
- `GET /api/2fa/qr-code`

    REQ
    ```json
     Content-Type: application/json
     Authorization: Bearer <JWT_TOKEN>
    ```

    RES
    ```json
     HTTP/1.1 200 OK
     Content-Type: application/json; charset=utf-8

     {
       "code": 200,
       "data": {
           "key": "KRPTKOGMNO...37A4OCD7FG3D",
           "url": "otpauth://totp/NethServer:root?algorithm=SHA1&digits=6&issuer=NethServer&period=30&secret=KRPTKOGMNO...37A4OCD7FG3D"
     },
        "message": "QR code string"
     }
    ```

### ubus
- `POST /api/ubus/call`

   REQ
    ```json
     Content-Type: application/json
     Authorization: Bearer <JWT_TOKEN>

     {
       "path": "luci",
       "method": "getRealtimeStats",
       "payload": {
           "mode": "conntrack"
        }
     }
    ```

    RES
    ```json
     HTTP/1.1 200 OK
     Content-Type: application/json; charset=utf-8

     {
       "code": 200,
       "data": {...},
       "message": "[UBUS] call action success"
     }
    ```
  ### Files
- `GET /api/files/<file_name>`

    REQ
    ```json
     Content-Type: application/json
     Authorization: Bearer <JWT_TOKEN>
    ```

    RES
    ```json
     HTTP/1.1 200 OK
     Content-Type: application/octet-stream
     Content-Length: <file_length>
     Content-Description: File Transfer
     Content-Disposition: attachment; filename=<file_name>
     Content-Transfer-Encoding: binary

     { [<file_length> bytes data] }
    ```

- `POST /api/files`

  REQ
  ```json
    Content-Length: 258
    Content-Type: multipart/form-data; boundary=------------------------c82dccb76d1cbe23
    Authorization: Bearer <JWT_TOKEN>

    file=@local_file
  ```

  RES
  ```json
    HTTP/1.1 200 OK
    Content-Type: application/json; charset=utf-8

    {
      "code": 200,
      "data": "upload-76cc70cc-8c71-40f5-b015-014c6061f7f4",
      "message": "file upload success"
    }

  ```
- `DELETE /api/files/<file_name>`

    REQ
    ```json
    Content-Type: application/json
    Authorization: Bearer <JWT_TOKEN>
    ```

    RES
    ```json
    HTTP/1.1 200 OK
    Content-Type: application/json; charset=utf-8

     {
       "code": 200,
       "data": false,
       "message": "file remove success"
     }
    ```
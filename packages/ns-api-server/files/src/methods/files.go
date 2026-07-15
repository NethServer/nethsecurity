/*
 * Copyright (C) 2024 Nethesis S.r.l.
 * http://www.nethesis.it - info@nethesis.it
 *
 * SPDX-License-Identifier: GPL-2.0-only
 *
 * author: Edoardo Spadoni <edoardo.spadoni@nethesis.it>
 */

package methods

import (
	"fmt"
	"net/http"
	"os"
	"path/filepath"
	"strings"

	"github.com/NethServer/nethsecurity-api/configuration"
	"github.com/NethServer/nethsecurity-api/response"
	"github.com/fatih/structs"
	"github.com/google/uuid"

	"github.com/gin-gonic/gin"
)

// safeFilePath joins baseDir and the user-supplied name, then verifies the
// cleaned result stays within baseDir. Returns false on traversal attempts.
func safeFilePath(baseDir, name string) (string, bool) {
	filePath := filepath.Join(baseDir, name) // Join cleans "../" segments
	if !strings.HasPrefix(filePath, baseDir+string(os.PathSeparator)) {
		return "", false
	}
	return filePath, true
}

func UploadFile(c *gin.Context) {
	//check limit size
	var w http.ResponseWriter = c.Writer
	c.Request.Body = http.MaxBytesReader(w, c.Request.Body, configuration.Config.UploadFileMaxSize*1024*1024)
	c.Next()

	// get file
	file, err := c.FormFile("file")

	// check error
	if err != nil {
		c.JSON(http.StatusBadRequest, structs.Map(response.StatusBadRequest{
			Code:    400,
			Message: "file upload error. error on upload",
			Data:    err.Error(),
		}))
		return
	}

	// create directory if not exists
	_ = os.MkdirAll(configuration.Config.UploadFilePath, os.ModePerm)

	// set name with uuid to avoid overrides
	name := "upload-" + uuid.New().String()

	// upload the file to specific directory and check error
	if err := c.SaveUploadedFile(file, configuration.Config.UploadFilePath+"/"+name); err != nil {
		c.JSON(http.StatusBadRequest, structs.Map(response.StatusBadRequest{
			Code:    400,
			Message: "file upload error. error on save",
			Data:    err.Error(),
		}))
		return
	}

	// return status ok
	c.JSON(http.StatusOK, structs.Map(response.StatusOK{
		Code:    200,
		Message: "file upload success",
		Data:    name,
	}))
}

func DownloadFile(c *gin.Context) {
	// get filename
	fileName := c.Param("filename")

	// compose filepath and reject path traversal attempts
	filePath, ok := safeFilePath(configuration.Config.DownloadFilePath, fileName)
	if !ok {
		c.JSON(http.StatusBadRequest, structs.Map(response.StatusBadRequest{
			Code:    400,
			Message: "invalid filename",
			Data:    fileName,
		}))
		return
	}

	// open file
	fileData, err := os.Open(filePath)
	if err != nil {
		c.JSON(http.StatusInternalServerError, structs.Map(response.StatusInternalServerError{
			Code:    500,
			Message: "file download error. error on read",
			Data:    err.Error(),
		}))
		return
	}
	defer fileData.Close()

	// get mimetype
	fileHeader := make([]byte, 512)
	_, err = fileData.Read(fileHeader)
	if err != nil {
		c.JSON(http.StatusInternalServerError, structs.Map(response.StatusInternalServerError{
			Code:    500,
			Message: "file download error. error on read mimetype",
			Data:    err.Error(),
		}))
		return
	}
	fileContentType := http.DetectContentType(fileHeader)

	// get file info
	fileInfo, err := fileData.Stat()
	if err != nil {
		c.JSON(http.StatusInternalServerError, structs.Map(response.StatusInternalServerError{
			Code:    500,
			Message: "file download error. error on read file info",
			Data:    err.Error(),
		}))
		return
	}

	// set header and return
	c.Header("Content-Description", "File Transfer")
	c.Header("Content-Transfer-Encoding", "binary")
	c.Header("Content-Disposition", "attachment; filename="+fileName)
	c.Header("Content-Type", fileContentType)
	c.Header("Content-Length", fmt.Sprintf("%d", fileInfo.Size()))
	c.File(filePath)
}

func DeleteFile(c *gin.Context) {
	// get filename
	fileName := c.Param("filename")

	// compose filepath and reject path traversal attempts
	filePath, ok := safeFilePath(configuration.Config.DownloadFilePath, fileName)
	if !ok {
		c.JSON(http.StatusBadRequest, structs.Map(response.StatusBadRequest{
			Code:    400,
			Message: "invalid filename",
			Data:    fileName,
		}))
		return
	}

	// remove file
	err := os.Remove(filePath)
	if err != nil {
		c.JSON(http.StatusInternalServerError, structs.Map(response.StatusInternalServerError{
			Code:    500,
			Message: "file remove error. error on remove file",
			Data:    err.Error(),
		}))
		return
	}

	// return ok
	c.JSON(http.StatusOK, structs.Map(response.StatusOK{
		Code:    200,
		Message: "file remove success",
		Data:    nil,
	}))
}

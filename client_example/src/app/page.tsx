"use client";

import { useState } from "react";

export default function HomePage({ }: {}) {

  // Defination for useState objects
  const [room, setRoom] = useState<string>("");
  const [name, setName] = useState<string>("");
  const [socket, setSocket] = useState<WebSocket | null>(null);
  const [isConnecting, setIsConnecting] = useState<boolean>(false);
  const [isSending, setIsSending] = useState<boolean>(false);
  const [messages, setMessages] = useState<string[]>([]);
  const [message, setMessage] = useState<string>("");
  const [connectionId, setConnectionId] = useState<number>(0);
  const [accessToken, setAccessToken] = useState<string>("");

  /** Called when the button "Connect" is clicked */
  const handleConnect = () => {
    setIsConnecting(true);

    // Check if `room` and `name` is empty
    if (room.trim().length === 0 || name.trim().length === 0) {
      alert("Room ID and Name are required");
      setRoom("");
      setName("");
      setIsConnecting(false);
      return;
    }

    // Call `createSocket` and then assign to `socket`
    createSocket({
      room: room.trim(),
      name: name.trim(),
      onConnectionInfoReceived: ({ id, token }) => {
        setConnectionId(id);
        setAccessToken(token);
      },
      onMessage: (event) => {
        setMessages((value) => {
          return [
            ...value,
            JSON.stringify(JSON.parse(event.data.toString()), null, 2)
          ];
        });
      },
      onClose: () => {
        setRoom("");
        setName("");
        setMessages([]);
        setSocket(null);
      },
    }).then(setSocket);

    setIsConnecting(false);
  };

  /** Called when the button "Disconnect" is clicked */
  const handleDisconnect = () => {
    socket?.close();
  };

  /** Called when the button "Send" is clicked */
  const handleSend = () => {
    setIsSending(true);

    // Check if the `message` is empty
    if (message.trim().length === 0) {
      alert("Message is required");
      setIsSending(false);
      return;
    }

    // Send the message to backend server
    fetch(`https://api.squidspirit.com/meet-parasite-backend/broadcast`, {
      method: "POST",
      // The content type must be set as "application/json"
      headers: {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + accessToken,
      },
      // Using JSON.stringify to serialize an object
      body: JSON.stringify({
        message: message.trim()
      }),
    });

    // Clear the input field
    setMessage("");
    setIsSending(false);
  };

  // JSX Content
  return (
    <div className="flex flex-col items-center p-8">
      <h1 className="font-bold text-4xl my-8">WebSocket Client</h1>
      {
        // Display when the socket hasn't been established
        socket === null &&
        <div className="flex flex-row items-center">
          <div className="grid grid-cols-[min-content_min-content] gap-2 m-4">
            <p className="text-nowrap">Room ID:</p>
            <input className="rounded-md text-black px-1" value={room} onChange={(e) => setRoom(e.target.value)}></input>
            <p className="text-nowrap">Name:</p>
            <input className="rounded-md text-black px-1" value={name} onChange={(e) => setName(e.target.value)}></input>
          </div>
          <button className="h-fit w-fit font-bold rounded-md border px-2 py-0.5" onClick={handleConnect} disabled={isConnecting}>Connect</button>
        </div>
      }
      {
        // Display when the socket has been established
        socket !== null &&
        <div className="flex flex-col w-screen items-center">
          <div className="flex flex-row gap-2 m-4">
            <p className="text-nowrap">Message:</p>
            <input className="rounded-md text-black px-1" value={message} onChange={(e) => setMessage(e.target.value)}></input>
            <button className="h-fit w-fit font-bold rounded-md border px-2 py-0.5" onClick={handleSend} disabled={isSending}>Send</button>
            <button className="h-fit w-fit font-bold rounded-md border px-2 py-0.5" onClick={handleDisconnect}>Disconnect</button>
          </div>
          <code className="m-4">
            <textarea className="rounded-md px-2 py-1" rows={24} cols={72} name="logs" id="logs" disabled={true} value={
              messages.map((message) => `${message}\n`).join("")
            }></textarea>
          </code>
          <p className="m-2">Room: {room}, Name: {name}, Connection ID: {connectionId}</p>
        </div>
      }
    </div>
  )
}

interface ConnectionInfo {
  id: number;
  token: string;
}

/** Create a socket with specified `room` and `name` */
async function createSocket({
  room,
  name,
  onConnectionInfoReceived,
  onMessage,
  onClose,
}: {
  /** The room ID to join (jmo-jsmh-iyo for example) */
  room: string,
  /** The name of the user */
  name: string,
  /** (Optional) The callback function to call when the connection ID received */
  onConnectionInfoReceived?: (info: ConnectionInfo) => void,
  /** (Optional) The callback function to call when messages received from the socket */
  onMessage?: (event: MessageEvent) => void,
  /** (Optional) The callback function to call when the socket is closed */
  onClose?: (event: CloseEvent) => void,
}): Promise<WebSocket> {
  return new Promise<WebSocket>((resolve, reject) => {
    const socket = new WebSocket(`wss://api.squidspirit.com/meet-parasite-backend/socket?room=${room}&name=${name}`);
    console.log("Connecting...");

    const timeout = setTimeout(() => {
      console.error("Connection timed out");
      socket.close();
      clearTimeout(timeout);
    }, 1000);

    socket.onopen = () => {
      console.log("Connection established");
      clearTimeout(timeout);
      resolve(socket);
    }

    socket.onerror = (error) => {
      socket.close();
      clearTimeout(timeout);
      reject(error)
    };

    socket.onclose = (event) => {
      console.log("Connection closed");
      if (onClose !== undefined)
        onClose(event);
    };

    var firstMessage = true;
    socket.onmessage = (event) => {
      if (firstMessage) {
        firstMessage = false;
        if (onConnectionInfoReceived !== undefined) {
          const payload = JSON.parse(event.data.toString());
          const id = payload["id"];
          const token = payload["token"];
          console.log("Connection ID:", id);
          console.log("Access token:", token);
          onConnectionInfoReceived({ id: id, token: token });
          return;
        }
      }
      console.log("Message received:", event.data.toString());
      if (onMessage !== undefined)
        onMessage(event);
    };
  });
}
"use client";

import { useState } from 'react';

type Props = {}

export default function HomePage({ }: Props) {
  const [room, setRoom] = useState<string>("");
  const [name, setName] = useState<string>("");
  const [socket, setSocket] = useState<WebSocket | null>(null);
  const [isConnecting, setIsConnecting] = useState<boolean>(false);
  const [isSending, setIsSending] = useState<boolean>(false);
  const [messages, setMessages] = useState<string[]>([]);
  const [message, setMessage] = useState<string>("");

  const handleConnect = () => {
    setIsConnecting(true);

    if (room.length === 0 || name.length === 0) {
      alert("Room ID and Name are required");
      setIsConnecting(false);
      return;
    }

    createSocket({
      room: room,
      name: name,
      onMessage: (event) => setMessages((value) => ([...value, event.data.toString()])),
      onClose: () => {
        setMessages([]);
        setSocket(null);
      },
    }).then(setSocket);

    setRoom("");
    setName("");
    setIsConnecting(false);
  };

  const handleDisconnect = () => {
    socket?.close();
  };

  const handleSend = () => {
    setIsSending(true);

    if (message.length === 0) {
      alert("Message is required");
      setIsSending(false);
      return;
    }

    fetch("http://localhost:8000/broadcast", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        message: message
      }),
    });

    setMessage("");
    setIsSending(false);
  };


  return (
    <div className="flex flex-col items-center p-8">
      <h1 className="font-bold text-4xl my-8">WebSocket Client</h1>
      {
        socket === null &&
        <div className="flex flex-row items-center">
          <div className="grid grid-cols-[min-content_min-content] gap-2 m-4">
            <p className="text-nowrap">Room ID:</p>
            <input className="rounded-md text-black" value={room} onChange={(e) => setRoom(e.target.value)}></input>
            <p className="text-nowrap">Name:</p>
            <input className="rounded-md text-black" value={name} onChange={(e) => setName(e.target.value)}></input>
          </div>
          <button className="h-fit w-fit font-bold rounded-md border px-2 py-0.5" onClick={handleConnect} disabled={isConnecting}>Connect</button>
        </div>
      }
      {
        socket !== null &&
        <div className="flex flex-col w-screen items-center">
          <div className="flex flex-row gap-2">
            <p className="text-nowrap">Message</p>
            <input className="rounded-md text-black" value={message} onChange={(e) => setMessage(e.target.value)}></input>
            <button className="h-fit w-fit font-bold rounded-md border px-2 py-0.5" onClick={handleSend} disabled={isSending}>Send</button>
            <button className="h-fit w-fit font-bold rounded-md border px-2 py-0.5" onClick={handleDisconnect}>Disconnect</button>
          </div>
          <textarea className="rounded-md w-[50%] m-4" rows={16} name="logs" id="logs" disabled={true} value={
            messages.map((message) => `${message}\n`).join("")
          }></textarea>
        </div>
      }
    </div>
  )
}

async function createSocket({
  room,
  name,
  onMessage,
  onClose,
}: {
  room: string,
  name: string,
  onMessage?: (event: MessageEvent) => void,
  onClose?: (event: CloseEvent) => void,
}): Promise<WebSocket> {
  return new Promise<WebSocket>((resolve, reject) => {
    const socket = new WebSocket(`ws://localhost:8000/socket?room=${room}&name=${name}`);
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

    socket.onmessage = (event) => {
      console.log("Message received:", event.data.toString());
      if (onMessage !== undefined)
        onMessage(event);
    };
  });
}